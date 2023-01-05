import frappe
import os
import shutil
from pymysql import ProgrammingError

error_title = "attach files"


def run_batch():
    print(f"start the batch")
    attach_files(source_files_root_path=frappe.get_site_path('public', 'files', 'items_pics'),
                 destination_doctype="Country",
                 destination_root_path=frappe.get_site_path('public', 'files'),
                 id_field_name="name",
                 main_file_field_name='image')
    print(f"end the batch")


# the source files has set of folders; each folder name is the doctype id
# all the files under tha folder will be attached to the doctype with that id
# the first file will be set as the main file (i.e.: employee profile pic, item's pic)
def attach_files(source_files_root_path: str, destination_root_path: str,
                 destination_doctype: str, id_field_name: str, main_file_field_name: str = None):
    limit_page_start = 0
    limit_page_length = 100
    docs = []
    while True:
        try:
            docs = frappe.get_all(destination_doctype,
                                  fields={"name"},  # FIXME: replace with the parameter
                                  limit_start=limit_page_start, limit_page_length=limit_page_length)
        except ProgrammingError as ex:
            frappe.log_error(message=f"error in getting the main data {format_exception(ex)}",
                             title=error_title)
            return

        try:
            for doc in docs:
                try:
                    doc_folder_name = (doc[id_field_name]).upper()
                    source_folder_path = f"{source_files_root_path}/{doc_folder_name}"
                    if not os.path.exists(source_folder_path):
                        frappe.log_error(message=f"doc id: {doc[id_field_name]},"
                                                 f" error: '{source_folder_path}' folder not found",
                                         title=error_title)
                        continue
                    files = get_folder_files(folder_path=source_folder_path)
                    first_file = True
                    for file in files:
                        new_file_name = f"{file}"  # TODO: may need to change the naming based on the case
                        destination_file_path = f"{destination_root_path}/{new_file_name}"
                        if copy_file(source_file_path=f"{source_folder_path}/{file}",
                                     destination_file_path=destination_file_path):

                            add_file_to_doc(file_path=destination_file_path,
                                            destination_doctype=destination_doctype,
                                            doc_id=doc[id_field_name],
                                            field_name=main_file_field_name,
                                            is_primary_file=first_file)
                            if first_file:
                                first_file = False

                except Exception as ex:
                    frappe.log_error(message=f"doc id: {doc[id_field_name]}, error: {format_exception(ex)}",
                                     title=error_title)
            limit_page_start += limit_page_length
        except Exception as ex:
            frappe.log_error(message=f"main docs loop error: {format_exception(ex)}",
                             title=error_title)


def add_file_to_doc(file_path: str, destination_doctype: str, doc_id: str, field_name: str = "image",
                    attachment_field_name: str = "attachment", is_private: int = 0, is_primary_file: bool = False):

    folder = 'Home/Attachments'
    file_name = get_file_name(file_path)
    file_url = get_file_url(file_full_path=file_path, file_name=file_name)
    file_doc = frappe.new_doc("File")
    file_doc.is_private = is_private
    file_doc.folder = folder
    file_doc.file_url = file_url
    file_doc.attached_to_doctype = destination_doctype
    file_doc.attached_to_name = doc_id
    file_doc.file_name = file_name
    file_doc.attached_to_field = attachment_field_name
    try:
        file_doc.insert()
    except Exception as ex:
        frappe.log_error(message=f"saving file error: '{format_exception(ex)}',"
                                 f" file_url: '{file_url}', folder: '{folder}',"
                                 f" file_path: '{file_path}', file_name: '{file_name}'",
                         title=error_title)
        return
    if is_primary_file:
        frappe.db.set_value(destination_doctype, doc_id, field_name, file_url)
    frappe.db.commit()


def get_folder_files(folder_path: str) -> []:
    files = []
    # Iterate directory
    for path in os.listdir(folder_path):
        # check if current path is a file
        if os.path.isfile(os.path.join(folder_path, path)):
            files.append(path)
    return files


def copy_file(source_file_path: str, destination_file_path: str) -> bool:
    is_succeeded = False
    try:
        shutil.copyfile(source_file_path, destination_file_path)
        is_succeeded = True
    except ProgrammingError as ex:
        frappe.log_error(message=f"trying to copy file from {source_file_path} to {destination_file_path} ,"
                                 f" error: {format_exception(ex)}",
                         title=error_title)
    return is_succeeded


def get_file_name(file_full_path: str):
    file_full_path = file_full_path.rstrip("/")
    file_path_segments = file_full_path.split("/")
    if len(file_path_segments) > 0:
        return file_path_segments[len(file_path_segments) - 1]
    return None


def get_parent_directory_path(file_path: str):
    file_name = get_file_name(file_full_path=file_path)
    parent_directory_path = file_path.rstrip(file_name)
    return parent_directory_path


def get_file_url(file_full_path: str, file_name: str, is_private: int = 0):
    site_name = frappe.utils.get_url()
    file_url = ""
    if is_private:
        file_url = f"{site_name}/private/files/{file_name}"
    else:
        file_url = f"{site_name}/public/files/{file_name}"

    file_url = file_url.replace('/./', '/')
    return file_url


def format_exception(ex: Exception) -> str:
    import traceback
    error = str(ex)
    trace = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
    return f'{error}\n{trace}'
