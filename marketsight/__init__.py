# shortcuts
from .methods import dataset, get_dataset, get_authorization_key,\
                     MarketsightAuthError, login_user

# constants
__major__ = 0  # for major interface/format changes
__minor__ = 1  # for minor interface/format changes
__release__ = 1  # for tweaks, bug-fixes, or development
__version__ = '%d.%d.%d' % (__major__, __minor__, __release__)
__author__ = 'Kieran Darcy'
__author_email__ = 'kdarcy@acritas.com'
__all__ = ('dataset','get_dataset','get_authorization_key','login_user','MarketsightAuthError')
