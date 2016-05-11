import base64
import datetime
import logging
import os.path
import urllib
import urlparse
import uuid
from collections import OrderedDict

import suds.client

from .config import URLS
from .helpers import datafile_to_base64, files_to_zipped_base64

#Enable SUDS logger
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

class MarketsightError(Exception): pass
class MarketsightAuthError(MarketsightError): pass


class MethodMixin(object):
    @classmethod
    def url(cls):
        return URLS.get(cls.__url__.lower())

    @classmethod
    def parse_list(cls, list_):
        if isinstance(list_, basestring):
            list_ = list_.split(',')
        return [('%s' % item).strip() for item in list_ if ('%s' % item).strip()]

    @classmethod
    def parse_datetime(cls, dt_string):
        return datetime.datetime.strptime(dt_string, '%m/%d/%Y %I:%M:%S %p')

    @property
    def client(self):
        if not hasattr(self, '_client'):
            self._client = suds.client.Client(self.url())
        return self._client

    def message(self, message):
        print(message)


class User(MethodMixin):
    __url__ = 'user'

    error_codes = {
        'A1': u'The credentials that were provided were not valid, or the user'\
        ' belongs to an account that is not authorized to use web services.',
        'U1': u'Unknown Error. This code will be returned for errors that do '\
        'not fall into any known category.'
    }

    def __init__(self, username, password, verbose=True):
        self.__username = username
        self.__password = password
        self.verbose = verbose

    def message(self, message):
        if self.verbose:
            print(message)

    @property
    def key(self):
        if not hasattr(self, '_key'):
            self._key = self.get_authorization_key()
        return self._key

    def refresh(self):
        try:
            delattr(self, '_key')
        except AttributeError:
            pass

    def get_authorization_key(self):
        self.message('...logging in as "%s"' % self.__username)
        key = self.client.service.GetAuthorizationKey(un=self.__username, \
                                                      pwd=self.__password)
        error = self.error_codes.get(key)
        if error:
            raise MarketsightAuthError(error)
        self.message('...success')
        return key

    def __repr__(self):
        return '<User(%r)>' % self.__username

    def __str__(self):
        return '%s' % self.__username

class Dataset(MethodMixin):
    __url__ = 'upload'

    def __init__(self, user, dataset=None, auto_login=True):
        if isinstance(user, User):
            self._user = user
        else:
            self._user = User(*user)

        self._dataset = None
        if dataset:
            self.dataset = dataset

        #Log in as user
        if auto_login:
            self.user.key

    def parse_dataset(self, dataset, raise_error=False):
        try:
            return '%s' % uuid.UUID(dataset)
        except TypeError:
            if raise_error:
                raise AttributeError('"%s" is not a valid MarketSight ID' % dataset)
        except ValueError:
            raise AttributeError('"%s" is not a valid MarketSight ID' % dataset)

    @property
    def user(self):
        return self._user

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        self._dataset = self.parse_dataset(dataset, raise_error=True)

    def select_dataset(self, dataset=None):
        """If the given "dataset" parameter is valid, return it - otherwise
        return self.dataset if one exists
        """
        if dataset is None and self.dataset is None:
            raise AttributeError('A valid dataset is required.')
        elif dataset is None:
            return self.dataset
        else:
            return self.parse_dataset(dataset, raise_error=True)

    def __repr__(self):
        return "<Dataset(user='%s', dataset='%s')>" % (self.user, self.dataset)

    def __upload(self, datafile_paths, navigator_path, datatype='spss'):
        datatypes = {
            #'spss': self.client.service.UploadDatasetDataSPSSZipped,
            #'sss': self.client.service.UploadDatasetDataTripleSZipped,
            'spss': self.client.service.UploadDatasetDataSPSSWithLabelsZipped,
            'sss': self.client.service.UploadDatasetDataTripleSWithLabelsZipped,
            }

        datatype_key = datatype.upper()
        try:
            datatype = datatypes[datatype.lower()]
        except KeyError:
            raise AttributeError('The "%s" data type is not allowed' % datatype)

        try:
            datafunction = datatype[function]
        except KeyError:
            raise AttributeError('"%s" is not a valid function method for %s data' %
                                (function, datatype_key))

        if isinstance(datafile_paths, basestring):
            datafile_paths = [datafile_paths, None]
        #datafile_path, metafile_path = datafile_paths

        self.message('...gathering %s data from "%s"' % (datatype_key, datafile_paths[0]))
        b64data = datafile_to_base64(datafile_paths, datatype=datatype_key)
        self.message('...uploading compressed %s data' % datatype_key)

        try:
            datafunction(key=self.user.key, datasetGuid=self.select_dataset(dataset),
                         zippedData=b64data)
        except suds.WebFault as details:
            self.message('An error ocurred\n%s' % details)
            return False
        return True

    def __update(self, datafile_paths, dataset=None, datatype='spss', function='update', save_as=None, zipped_file=None):
        datatypes = {
            'spss': {
                #'update': self.client.service.UpdateDatasetDataSPSSZipped,
                'update': self.client.service.UpdateDatasetDataSPSSWithLabelsZipped,
                'append': self.client.service.AppendDatasetDataSPSSZipped,
            },
            'sss': {
                #'update': self.client.service.UpdateDatasetDataTripleSZipped,
                'update': self.client.service.UpdateDatasetDataTripleSWithLabelsZipped,
                'append': self.client.service.AppendDatasetDataTripleSZipped,
            },
        }

        if zipped_file is None:

            datatype_key = datatype.upper()
            try:
                datatype = datatypes[datatype.lower()]
            except KeyError:
                raise AttributeError('The "%s" data type is not allowed' % datatype)

            try:
                datafunction = datatype[function]
            except KeyError:
                raise AttributeError('"%s" is not a valid function method for %s data' %
                                    (function, datatype_key))

            if isinstance(datafile_paths, basestring):
                datafile_paths = [datafile_paths, None, None]
            if len(datafile_paths) == 2:
                datafile_paths.append(None)
            labelsfile_path = datafile_paths.pop(2)

            self.message('...gathering %s data from "%s"' % (datatype_key, datafile_paths[0]))
            b64data = datafile_to_base64(datafile_paths, datatype=datatype_key, save_as=save_as)
            labels_b64data = None
            if labelsfile_path:
                self.message('...gathering labels XML data')
                labels_b64data = files_to_zipped_base64([labelsfile_path])
                self.message('...uploading compressed %s data' % datatype_key)

        else:
            self.message('...uploading compressed data from zipped file')
            b64Data = zipped_file

        try:
            if function == 'update':
                datafunction(key=self.user.key, datasetGuid=self.select_dataset(dataset),
                             zippedData=b64data, zippedVarLabeling=labels_b64data)
            else:
                datafunction(key=self.user.key, datasetGuid=self.select_dataset(dataset),
                             zippedData=b64data)
        except suds.WebFault as details:
            self.message('An error ocurred\n%s' % details)
            return False
        return True

    def __append(self, datafile_paths, dataset=None, datatype='spss', save_as=None):
        return self.__update(datafile_paths=datafile_paths, dataset=dataset,
                             datatype=datatype, function='append', save_as=save_as)

    def number_of_respondents(self, dataset=None):
        try:
            return int(self.client.service.GetNumberOfRespondents(
                        key=self.user.key, datasetGuid=self.select_dataset(dataset)))
        except suds.WebFault as details:
            self.message('An error ocurred\n%s' % details)

    def last_uploaded_datetime(self, dataset=None):
        try:
            return self.parse_datetime(
            self.client.service.GetLastUploadedDateTimeByGuid(key=self.user.key,
                                        datasetGuid=self.select_dataset(dataset)))
        except suds.WebFault as details:
            self.message('An error ocurred\n%s' % details)

    def check_for_missing_variables(self, variables, dataset=None):
        try:
            return self.parse_list(
            self.client.service.CheckForMissingVariables(key=self.user.key,
                            datasetGuid=self.select_dataset(dataset),
                            variableList=','.join(self.parse_list(variables))))
        except suds.WebFault as details:
            self.message('An error ocurred\n%s' % details)

    def update_spss(self, datafile_path, dataset=None, save_as=None):
        return self.__update(datafile_path, dataset=dataset, save_as=save_as)

    def append_spss(self, datafile_path, dataset=None, save_as=None):
        return self.__append(datafile_path, dataset=dataset, save_as=save_as)

    #def update_spss_zipped(self, datafile_path, dataset=None):
    #    if not os.path.splitext(datafile_path)[1].lower().endswith('.zip'):
    #        raise AttributeError('Please specify a ZIP file')
    #    return self.update_spss(datafile_path=datafile_path, dataset=dataset)

    #def append_spss_zipped(self, datafile_path, dataset=None):
    #    if not os.path.splitext(datafile_path)[1].lower().endswith('.zip'):
    #        raise AttributeError('Please specify a ZIP file')
    #    return self.append_spss(datafile_path=datafile_path, dataset=dataset)

    def update_sss(self, metadatafile_path, datafile_path, labelsfile_path=None, dataset=None, save_as=None, zipped_file=None):
        datafile = [datafile_path, metadatafile_path, labelsfile_path]
        return self.__update(datafile, dataset=dataset, datatype='sss', save_as=save_as, zipped_file=zipped_file)

    def append_sss(self, metadatafile_path, datafile_path, dataset=None, save_as=None):
        datafile = [datafile_path, metadatafile_path]
        return self.__append(datafile, dataset=dataset, datatype='sss', save_as=save_as)

    #def update_sss_zipped(self, datafile_path, dataset=None):
    #    if not os.path.splitext(datafile_path)[1].lower().endswith('.zip'):
    #        raise AttributeError('Please specify a ZIP file')
    #    return self.update_sss(datafile_path=datafile_path, dataset=dataset)

    #def append_sss_zipped(self, datafile_path, dataset=None):
    #    if not os.path.splitext(datafile_path)[1].lower().endswith('.zip'):
    #        raise AttributeError('Please specify a ZIP file')
    #    return self.append_sss(datafile_path=datafile_path, dataset=dataset)


class ReportURL(object):
    """A convience class for construction of Remote Report Access URLS"""
    base_url = URLS.get('reports')
    export_types = {
        'crosstab': ('excel', 'excel2007', 'pdf', 'etabs'),
        'datatable': ('excel', 'excel2007'),
        'chart': ('image', 'excel', 'powerpoint', 'powerpoint2007'),
        }
    modes = {
        'marketsight': 'MarketSight', 'fullwindow': 'FullWindow',
        'external': 'External', 'readonly': 'ReadOnly'
        }
    url_types = ('dataset','chart','datatable','crosstab','file')

    @classmethod
    def parse_list(cls, list_):
        if isinstance(list_, basestring):
            list_ = list_.split(',')
        return [('%s' % item).strip() for item in list_ if ('%s' % item).strip()]

    @classmethod
    def parse_id(cls, id):
        try:
            return '%s' % uuid.UUID(id)
        except TypeError:
            raise AttributeError('"%s" is not a valid MarketSight ID' % id)
        except ValueError:
            raise AttributeError('"%s" is not a valid MarketSight ID' % id)

    def __init__(self, url_type, id, user=None, mode=None, export=None, rows=None, columns=None):
        self.url_type = url_type
        self.user = user
        self.mode = mode
        self.id = id
        self.export = export
        self.query = {}
        self.rows = rows
        self.columns = columns

    @property
    def ak(self):
        #if self.mode.lower() not in ('MarketSight', 'FullWindow'):
        if self.user is not None:
            return self.user.key
        return None

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if id is None:
            raise AtributeError("You must specify an ID.")
        self._id = self.parse_id(id)

    def id_key(self):
        if self.url_type == 'dataset':
            return 'datasetid'
        return 'id'

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = self.modes.get(mode.lower(),'ReadOnly')

    @property
    def url_type(self):
        return self._url_type

    @url_type.setter
    def url_type(self, url_type):
        if url_type.lower() in self.url_types:
            self._url_type = url_type.lower()
        else:
            raise AttributeError('"%s" is an unknown URL type.' % url_type)

    @property
    def export(self):
        return self._export

    @export.setter
    def export(self, export):
        if export is not None:
            try:
                self._export = self.export_types[self.url_type]
            except KeyError:
                raise AttributeError('"%s" is not a valid export type for a %s' % (export, self.url_type))
        else:
            self._export = None

    def geturl(self):
        self.query.update(mode=self.mode)
        if self.rows:
            self.query.update(rows=self.rows)
        if self.columns:
            self.query.update(rows=self.columns)
        if self.export:
            self.query.update(export=self.export)
        if self.ak:
            self.query.update(ak=self.ak)
        if self.id:
            self.query.pop('datasetid', None)
            self.query.update({self.id_key(): self.id})
        return urlparse.urljoin(self.base_url, '?{}'.format(urllib.urlencode(self.query)))


class Report(object):
    url_factory = ReportURL

    def __init__(self, user=None):
        self.user = user

    def chart(self, id, mode='ReadOnly', export=None):
        url = self.url_factory('chart', id, user=self.user, mode=mode, export=export)
        return url.geturl()

    def datatable(self, id, mode='ReadOnly', export=None):
        url = self.url_factory('datatable', id, user=self.user, mode=mode, export=export)
        return url.geturl()


# Factory shortcuts
def dataset(username, password, dataset=None):
    return Dataset((username, password), dataset)

def get_dataset(details_file):
    details = [line.strip() for line in open(details_file,'r').readlines() if line.strip()]
    return dataset(*details)

def login_user(username, password):
    """Log a user into Marketsight and return a user object is succesful.
    if an authentication error ocurrs, then return None"""
    user = User(username, password, verbose=False)
    try:
        key = user.get_authorization_key()
    except MarketsightAuthError:
        user = None
    return user

def get_authorization_key(username, password):
    user = login_user(username, password)
    return user.key
