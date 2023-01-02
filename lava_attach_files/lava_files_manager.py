import frappe
import os
import shutil
from pymysql import ProgrammingError

error_title = "attach files"


def run_batch():
    # TODO: update the pah

    attach_files(source_files_root_path="public/items_pics",
                 destination_doctype="Item",
                 destination_root_path= "/public/files",
                 id_field_name="name")


# the source files has set of folders; each folder name is the doctype id
# all the files under tha folder will be attached to the doctype with that id
# the first file will be set as the main file (i.e.: employee profile pic, item's pic)
def attach_files(source_files_root_path: str, destination_root_path: str, destination_doctype: str, id_field_name: str):
    limit_page_start = 0
    limit_page_length = 100
    while True:
        try:
            docs = frappe.get_all(f" SELECT $(id_field)s from `tab$(doctype)s`",
                                  {'doctype': destination_doctype, "id_field": id_field_name},
                                  limit_start=limit_page_start, limit_page_length=limit_page_length)
            for doc in docs:
                # FIXME: fix the paths
                try:
                    source_folder_path = source_files_root_path + "/" + doc[id_field_name]
                    files = get_folder_files(source_folder_path=source_folder_path)
                    first_file = True
                    for file in files:
                        destination_file_path = destination_root_path + "/" + file
                        if copy_file(source_file_path=source_folder_path + "/" + file,
                                     destination_file_path=destination_file_path):
                            if first_file:
                                add_file_to_doc(file_path=destination_file_path,
                                                destination_doctype=destination_doctype,
                                                field_name=id_field_name)
                                first_file = False
                            else:
                                add_file_to_doc(file_path=destination_file_path,
                                                destination_doctype=destination_doctype,
                                                field_name=None)
                except ProgrammingError as ex:
                    frappe.log_error(message=f"doc id: {doc[id_field_name]}, error: {format_exception(ex)}",
                                     title=error_title)
            limit_page_start += limit_page_length
        except ProgrammingError as ex:
            frappe.log_error(message=f"main docs loop error: {format_exception(ex)}",
                             title=error_title)


def add_file_to_doc(file_path: str, destination_doctype: str, field_name: str = None):
    # TODO: check if the file path is unique, in the used method by default
    file_doc = frappe.new_doc("File")
    file_doc.file_url = file_path
    file_doc.attached_to_doctype = destination_doctype
    if field_name:
        file_doc.attached_to_field = field_name
    file_doc.insert()


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


def format_exception(ex: Exception) -> str:
    import traceback
    error = str(ex)
    trace = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
    return f'{error}\n{trace}'
