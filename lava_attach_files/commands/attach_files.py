import click
import frappe
from frappe.commands import pass_context

from lava_attach_files.lava_files_manager import attach_files as do_attach_files


@click.command('attach-files')
@click.option('--source', help='Source directory', prompt=True, required=True)
@click.option('--doctype', help='Target doctype', prompt=True, required=True)
@click.option('--id-field', help='ID field', prompt=True, required=True)
@click.option('--image-field', help='Image field', prompt=True, required=True)
@click.option('--private', default=False, help='Make uploaded files private')
@pass_context
def attach_files(ctx, source: str, doctype: str, id_field: str, image_field: str, private: bool) -> None:
    if not ctx.sites:
        print('No sites defined')
        return

    site = ctx.sites[0]
    print(f'Running for site: {site}')
    frappe.init(site)
    if not frappe.db:
        frappe.connect(site)

    do_attach_files(source_files_root_path=source,
                    destination_doctype=doctype,
                    destination_root_path=frappe.get_site_path('private' if private else 'public', 'files'),
                    id_field_name=id_field,
                    main_file_field_name=image_field)
