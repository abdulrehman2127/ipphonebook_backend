import os
import csv
import io
import xml.etree.ElementTree as ET
from django.http import FileResponse, HttpResponseNotFound
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import PhoneRequestLog
from .serializers.api_serializer import PhoneRequestLogSerializer

BASE_FILE_PATH = os.path.join(os.getcwd(), "phone_files")
print(BASE_FILE_PATH)

def get_client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    if ip and ',' in ip:
        ip = ip.split(',')[0]
    return ip



# This Feature is currently disable at both Frontend and Backend     ----->
# -------------------------------
# NEW: Read Phonebook as JSON
# -------------------------------
class ReadPhonebookJSON(APIView):
    """
    Reads the corporate_phonebook.xml file and returns it as JSON.
    """
    def get(self, request):
        filename = "corporate_phonebook.xml"
        file_path = os.path.join(BASE_FILE_PATH, filename)
        if not os.path.exists(file_path):
            return Response({"error": f"File '{filename}' not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()           
            entries = []
            for entry in root.findall('DirectoryEntry'):
                name_elem = entry.find('Name')
                tel_elem = entry.find('Telephone')
                dept_elem = entry.find('Department')
                entries.append({
                    'name': name_elem.text if name_elem is not None else '',
                    'telephone': tel_elem.text if tel_elem is not None else '',
                    'department': dept_elem.text if dept_elem is not None else ''
                })         
            return Response({'entries': entries}, status=status.HTTP_200_OK)      
        except ET.ParseError as e:
            return Response({"error": f"XML parsing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error reading file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -------------------------------
# NEW: Write Phonebook from JSON
# -------------------------------
class WritePhonebookJSON(APIView):
    """
    Accepts JSON data and writes it to corporate_phonebook.xml.
    """
    def post(self, request):
        filename = "corporate_phonebook.xml"
        file_path = os.path.join(BASE_FILE_PATH, filename)      
        data = request.data       
        if 'entries' not in data:
            return Response({"error": "Missing 'entries' field in request"}, status=status.HTTP_400_BAD_REQUEST)       
        try:
            root = ET.Element('YealinkIPPhoneDirectory')
            for entry_data in data['entries']:
                entry = ET.SubElement(root, 'DirectoryEntry')
                name = ET.SubElement(entry, 'Name')
                name.text = entry_data.get('name', '')
                telephone = ET.SubElement(entry, 'Telephone')
                telephone.text = entry_data.get('telephone', '')
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")  
            with open(file_path, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)       
            return Response({"message": "Phonebook updated successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": f"Error writing file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# <--------


# -------------------------------
# NEW: Add Single Phonebook Entry
# -------------------------------
class AddPhonebookEntry(APIView):
    """
    Adds a single entry to corporate_phonebook.xml.
    """
    def post(self, request):
        filename = "corporate_phonebook.xml"
        file_path = os.path.join(BASE_FILE_PATH, filename)      
        data = request.data       
        if 'name' not in data or 'telephone' not in data:
            return Response(
                {"error": "Missing 'name' or 'telephone' field in request"}, 
                status=status.HTTP_400_BAD_REQUEST
            )      
        name = data.get('name', '').strip()
        telephone = data.get('telephone', '').strip()
        department = data.get('department', '').strip()       
        if not name or not telephone:
            return Response(
                {"error": "Name and telephone cannot be empty"}, 
                status=status.HTTP_400_BAD_REQUEST
            )      
        try:
            if os.path.exists(file_path):
                tree = ET.parse(file_path)
                root = tree.getroot()
            else:
                root = ET.Element('YealinkIPPhoneDirectory')
                tree = ET.ElementTree(root)          
            entry = ET.SubElement(root, 'DirectoryEntry')
            name_elem = ET.SubElement(entry, 'Name')
            name_elem.text = name
            telephone_elem = ET.SubElement(entry, 'Telephone')
            telephone_elem.text = telephone
            if department:
                dept_elem = ET.SubElement(entry, 'Department')
                dept_elem.text = department
            ET.indent(tree, space="  ")
            with open(file_path, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)
            return Response(
                {
                    "message": "Entry added successfully",
                    "entry": {
                        "name": name, 
                        "telephone": telephone,
                        "department": department
                    }
                }, 
                status=status.HTTP_201_CREATED
            )      
        except ET.ParseError as e:
            return Response(
                {"error": f"XML parsing error: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error adding entry: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# -------------------------------
# NEW: Import CSV and Convert to XML
# -------------------------------
class ImportCSVToXML(APIView):
    """
    Accepts a CSV file upload and converts it to XML format.
    Replaces the content of corporate_phonebook.xml.
    
    CSV Format: Name,Telephone,Department
    Optional fields: Department
    """
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        filename = "corporate_phonebook.xml"
        file_path = os.path.join(BASE_FILE_PATH, filename)
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file uploaded. Please provide a CSV file."},
                status=status.HTTP_400_BAD_REQUEST
            )       
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            return Response(
                {"error": "Invalid file format. Please upload a CSV file."},
                status=status.HTTP_400_BAD_REQUEST
            )      
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            required_fields = ['Name', 'Telephone']
            optional_fields = ['Department']           
            if not all(field in csv_reader.fieldnames for field in required_fields):
                return Response(
                    {
                        "error": f"CSV must contain required columns: {', '.join(required_fields)}",
                        "found_columns": csv_reader.fieldnames
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            root = ET.Element('YealinkIPPhoneDirectory')
            entries_count = 0           
            for row in csv_reader:
                if not row.get('Name') or not row.get('Telephone'):
                    continue
                entry = ET.SubElement(root, 'DirectoryEntry')
                name = ET.SubElement(entry, 'Name')
                name.text = row['Name'].strip()
                telephone = ET.SubElement(entry, 'Telephone')
                telephone.text = row['Telephone'].strip()
                if 'Department' in row and row['Department'].strip():
                    department = ET.SubElement(entry, 'Department')
                    department.text = row['Department'].strip()              
                entries_count += 1          
            if entries_count == 0:
                return Response(
                    {"error": "No valid entries found in CSV file"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            with open(file_path, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)           
            return Response(
                {
                    "message": "CSV imported and converted to XML successfully",
                    "entries_imported": entries_count,
                    "file": filename
                },
                status=status.HTTP_200_OK
            )      
        except csv.Error as e:
            return Response(
                {"error": f"CSV parsing error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except UnicodeDecodeError as e:
            return Response(
                {"error": "File encoding error. Please ensure the file is UTF-8 encoded."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error processing file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# -------------------------------
# Serve file based on filename
# -------------------------------
def serve_file_download(request, filename):
    ip_address = get_client_ip(request)
    file_path = os.path.join(BASE_FILE_PATH, filename)

    if os.path.exists(file_path):
        PhoneRequestLog.objects.create(
            ip_address=ip_address,
            file_requested=filename,
            status_code=200,
            timestamp=timezone.now()
        )
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    else:
        PhoneRequestLog.objects.create(
            ip_address=ip_address,
            file_requested=filename,
            status_code=404,
            timestamp=timezone.now()
        )
        return HttpResponseNotFound(f"File '{filename}' not found.")




class ServeFiles(APIView):
    BASE_FILE_PATH = os.path.join(os.getcwd(), "phone_files")
    ALLOWED_FILES = [
        'f0DPH-150GEhw1.100.cfg',
        'a09f7a58f99f.cfg',
        'corporate_phonebook.xml'
    ]

    def get(self, request, filename):
        ip_address = get_client_ip(request)
        if filename not in self.ALLOWED_FILES:
            return Response({"error": "File not allowed"}, status=status.HTTP_404_NOT_FOUND)

        file_path = os.path.join(self.BASE_FILE_PATH, filename)
        if not os.path.exists(file_path):
            return Response({"error": f"File '{filename}' not found"}, status=status.HTTP_404_NOT_FOUND)
        PhoneRequestLog.objects.create(
            ip_address=ip_address,
            file_requested=filename,
            status_code=200,
            timestamp=timezone.now()
        )
        content_type = 'text/plain'
        if filename.endswith('.xml'):
            content_type = 'text/xml'
        elif filename.endswith('.cfg'):
            content_type = 'text/plain'

        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    
    
# -------------------------------
# API endpoint: logs
# -------------------------------
class PhoneRequestLogList(APIView):
    def get(self, request):
        logs = PhoneRequestLog.objects.all().order_by('-timestamp')
        serializer = PhoneRequestLogSerializer(logs, many=True)
        return Response(serializer.data)
