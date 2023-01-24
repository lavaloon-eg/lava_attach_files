import sys
from typing import List, Dict

import frappe
import os
import shutil


# the source files has set of folders; each folder name is the doctype id
# all the files under tha folder will be attached to the doctype with that id
# the first file will be set as the main file (i.e.: employee profile pic, item's pic)
def attach_files(source_files_root_path: str, destination_root_path: str,
                 destination_doctype: str, id_field_name: str, main_file_field_name: str = None):
    if not os.path.exists(source_files_root_path):
        log_error(f"error: '{source_files_root_path}' folder not found")
        return

    doc_to_file_map = prepare_doc_to_file_map(source_files_root_path, destination_root_path)

    limit_page_start = 0
    limit_page_length = 100
    while True:
        docs = frappe.get_all(destination_doctype, filters={id_field_name: ['is', 'set']},
                              fields=[id_field_name],
                              limit_start=limit_page_start, limit_page_length=limit_page_length)
        if not docs:
            break

        for doc in docs:
            print(f"Processing: {doc[id_field_name]}")
            docname = frappe.db.get_value(destination_doctype, filters={id_field_name: doc[id_field_name]},
                                          fieldname='name')
            try:
                files = doc_to_file_map.get(doc[id_field_name], [])
                for file in files:
                    is_primary = file['is_primary']
                    destination_file_path = file['destination_file_path']
                    add_file_to_doc(file_path=destination_file_path,
                                    destination_doctype=destination_doctype,
                                    doc_id=docname,
                                    field_name=main_file_field_name,
                                    is_primary_file=is_primary)
            except Exception as ex:
                log_error(f"doc id: {doc[id_field_name]}, error: {format_exception(ex)}")
        limit_page_start += limit_page_length


def prepare_doc_to_file_map(source_files_root_path: str, destination_root_path: str) -> Dict[str, List[dict]]:
    result = {}
    files = get_folder_files(source_files_root_path)
    print(f'Processing {len(files)} file(s)')
    for index, file in enumerate(files):
        print(f'File {index + 1}/{len(files)}')
        filename = os.path.splitext(file)[0]
        last_underscore_index = filename.rfind('_')
        if last_underscore_index == -1:
            log_error(f"Skipping file '{file}' because it contains no underscores")
            continue
        key = filename[:last_underscore_index]
        is_primary = filename.endswith('_1')
        new_file_name = f"{file}"  # TODO: may need to change the naming based on the case
        destination_file_path = os.path.join(destination_root_path, new_file_name)
        if copy_file(source_file_path=os.path.join(source_files_root_path, file),
                     destination_file_path=destination_file_path):
            if key not in result:
                result[key] = []
            result[key].append({
                'is_primary': is_primary,
                'new_file_name': new_file_name,
                'destination_file_path': destination_file_path
            })

    return result


def add_file_to_doc(file_path: str, destination_doctype: str, doc_id: str, field_name: str = "image",
                    attachment_field_name: str = "attachment", is_private: int = 0, is_primary_file: bool = False):
    file_name = os.path.basename(file_path)
    file_url = os.path.join('/files', file_name)
    if frappe.db.sql('SELECT name FROM tabFile WHERE file_url = %(url)s AND attached_to_doctype = %(doctype)s AND '
                     'attached_to_name = %(docname)s', {'url': file_url, 'doctype': destination_doctype,
                                                        'docname': doc_id}):
        print(f"Skipping {file_name} for {doc_id} because it's already attached")
        return

    folder = 'Home/Attachments'
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
        log_error(f"saving file error: '{format_exception(ex)}',"
                  f" file_url: '{file_url}', folder: '{folder}',"
                  f" file_path: '{file_path}', file_name: '{file_name}'")
        return
    if is_primary_file:
        frappe.db.set_value(destination_doctype, doc_id, field_name, file_url)
    frappe.db.commit()


def get_folder_files(folder_path: str) -> []:
    return [path for path in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, path))]


def copy_file(source_file_path: str, destination_file_path: str) -> bool:
    try:
        shutil.copyfile(source_file_path, destination_file_path)
        return True
    except shutil.Error as ex:
        log_error(f"trying to copy file from {source_file_path} to {destination_file_path} ,"
                  f" error: {format_exception(ex)}")
        return False


def log_error(message: str) -> None:
    print(message, file=sys.stderr)


def format_exception(ex: Exception) -> str:
    import traceback
    error = str(ex)
    trace = ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))
    return f'{error}\n{trace}'
