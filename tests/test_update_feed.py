import importlib.util
import os
import xml.etree.ElementTree as ET

D = os.path.join(os.path.dirname(__file__), '..', 'adapters', 'libreoffice', 'xproofreader')
spec = importlib.util.spec_from_file_location('make_update_xml', os.path.join(D, 'make_update_xml.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

XLINK = '{http://www.w3.org/1999/xlink}href'
UPD = '{http://openoffice.org/extensions/update/2006}'
DESC = '{http://openoffice.org/extensions/description/2006}'


def test_description_points_to_latest_release_feed():
    root = ET.parse(os.path.join(D, 'description.xml')).getroot()
    src = root.find(DESC + 'update-information/' + DESC + 'src')
    assert src.get(XLINK) == ('https://github.com/ollisulopuisto/punakyna/releases/latest/download/'
                              'punakyna.update.xml')


def test_update_xml_matches_description_version_and_tag():
    ident, version = mod.read_description()
    root = ET.fromstring(mod.build('v9.9.9'))
    assert root.find(UPD + 'identifier').get('value') == ident
    assert root.find(UPD + 'version').get('value') == version
    href = root.find(UPD + 'update-download/' + UPD + 'src').get(XLINK)
    assert href == ('https://github.com/ollisulopuisto/punakyna/releases/download/v9.9.9/'
                    'punakyna-full-macos.oxt')
