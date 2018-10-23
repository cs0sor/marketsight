import os

URLS = {
    'user':   os.environ.get('MARKETSIGHT_USER_ENDPOINT', 'https://application.marketsight.com/MarketSightWebServices/DatasetUploadAuthorizationService.asmx?WSDL'),
    'upload': os.environ.get('MARKETSIGHT_UPLOAD_ENDPOINT', 'https://application.marketsight.com/MarketSightWebServices/DatasetUploadService.asmx?WSDL'),
    'reports': os.environ.get('MARKETSIGHT_REVIEW_ENDPOINT', 'https://application.marketsight.com/MktgWorksite/ItemView.aspx'),
}
