from django.urls import path
from .views import (
    serve_file_download, 
    PhoneRequestLogList,
    ServeFiles,
    ReadPhonebookJSON,
    WritePhonebookJSON,
    AddPhonebookEntry,
    ImportCSVToXML
)

urlpatterns = [
    path('phonebook/add-entry/', AddPhonebookEntry.as_view(), name='add_phonebook_entry'),
    path('phonebook/import-csv/', ImportCSVToXML.as_view(), name='import_csv_to_xml'),
    path('files/download/<str:filename>', serve_file_download, name='serve_file_download'),
    path('logs/logs/', PhoneRequestLogList.as_view(), name='phone_request_logs'),
    path('<str:filename>', ServeFiles.as_view(), name='serve_file'),
     #Currently Disabled
    path('phonebook/read/', ReadPhonebookJSON.as_view(), name='read_phonebook_json'),
    path('phonebook/write/', WritePhonebookJSON.as_view(), name='write_phonebook_json'),

]
