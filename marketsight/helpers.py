import os
import zipfile
import StringIO
import base64


def files_to_zipped_data(filenames):
    files_to_zip = []

    for filename in filenames:
        full_filename = os.path.realpath(filename)
        filepath, short_filename = os.path.split(full_filename)
        files_to_zip.append((full_filename, short_filename))

    datafile_zipped = StringIO.StringIO()
    with zipfile.ZipFile(datafile_zipped, mode='w') as zipper:
        for f,fn in files_to_zip:
            zipper.write(f, arcname=fn, compress_type=zipfile.ZIP_DEFLATED)
    data = datafile_zipped.getvalue()
    datafile_zipped.close()

    return data

def files_to_zipped_base64(filenames):
    data = files_to_zipped_data(filenames)
    return base64.b64encode(data)

def datafile_to_base64(datafile_paths, datatype='spss', save_as=None):
    if isinstance(datafile_paths, basestring):
        datafile_paths = [datafile_paths,None]
    datafile_path, metadatafile_path = datafile_paths
    datatypes = {
        'spss': {'data':('.sav',)}, 
        'sss': {'metadata':'.sss', 'data':('.asc','.csv')},
        }

    if datatype.lower() not in datatypes:
        raise AttributeError('The "%s" data type is not allowed' % datatype)
    datatype_key = datatype.upper()
    datatype = datatypes[datatype.lower()]

    datafile = os.path.realpath(datafile_path)
    filepath, datafile_name = os.path.split(datafile)
    basename, datafile_ext = os.path.splitext(datafile_name)
    is_already_zip = datafile_ext.lower() == '.zip'
    if not is_already_zip and datafile_ext.lower() not in datatype['data']:
        raise AttributeError('The %s data file must have the extension "%s".' \
                             % (datatype_key, ' or '.join(datatype['data'])))
    files_to_send_to_zip = [datafile]

    if datatype.get('metadata'):
        if metadatafile_path:
            if is_already_zip:
                raise AttributeError("A ZIP file doesn't require a metadata file.")

            metadatafile = os.path.realpath(metadatafile_path)
            filepath, metadatafile_name = os.path.split(metadatafile)
            basename, metadatafile_ext = os.path.splitext(metadatafile_name)
            if metadatafile_ext.lower() <> datatype['metadata']:
                raise AttributeError('The %s metadata file must have the extension "%s".'\
                                     % (datatype_key, datatype['metadata']))
            files_to_send_to_zip.append(metadatafile)
        else:
            if not is_already_zip:
                raise AttributeError('The %s data type requires a "%s" metadata file.'\
                                     % (datatype_key, datatype['metadata']))

    if is_already_zip:
        with zipfile.ZipFile(datafile, mode='r') as datafile_zipped:
            files_in_zip = [os.path.splitext(f)[1].lower() for f in datafile_zipped.namelist()]
            if not set(datatype.values()) == set(files_in_zip):
                raise TypeError('An %s ZIP file only allows one %s file.' % (datatype_key, ' and '.join(datatype.values())))

        with open(datafile,'rb') as f:
            f.seek(0)
            data = f.read()
    else:
        data = files_to_zipped_data(files_to_send_to_zip)

    if save_as:
        with open(save_as, 'wb') as outfile:
            outfile.write(data)

    return base64.b64encode(data)
