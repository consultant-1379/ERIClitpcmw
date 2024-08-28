import copy
import os
import lxml.etree as xml

from cmwplugin.campaign import cmw_constants
from litp.core.litp_logging import LitpLogger
log = LitpLogger()


class cmwETF(object):

    def __init__(self, sg_obj):
        self.sg = sg_obj
        self.etf_xml = ''
        self.path = os.path.join(cmw_constants.LITP_DATA_DIR,
                                 "ETF_%s.xml" % sg_obj.name)

    def write_to_disk(self):
        with open(self.path, "w") as f:
            f.write(self.etf_xml)


class cmwETFGenerator(object):

    def __init__(self):
        path = os.path.dirname(cmw_constants.__file__)
        _template = os.path.join(path, "./templates/ETF_template.xml")
        self.template_file = open(_template, "r")
        self.base_xml = self.template_file.read()

    def generate_sg_etf(self, sg_obj, campaign_name, provider="3PP"):
        # TODO: remove file handling from this function
        # make it return just a XML string.
        comp_type_template = cmw_constants.COMPTYPE_ETF_TEMPLATE
        apptype_version = '1.0.0'
        gen_xml = copy.copy(self.base_xml)
        avail_model = cmw_constants.REDUNDANCY_MODEL[sg_obj.availability_model]

        gen_xml = gen_xml.replace("$name", campaign_name)
        gen_xml = gen_xml.replace("$provider", provider)
        gen_xml = gen_xml.replace("$version", apptype_version)
        gen_xml = gen_xml.replace("$entityTypesFile_name", "$name")
        gen_xml = gen_xml.replace("$AVAILABILITY_MODEL", avail_model)
        gen_xml = gen_xml.replace("$AppType_name", sg_obj.app_name)
        gen_xml = gen_xml.replace("$SgType_name", "%s-SgType" % sg_obj.name)
        gen_xml = gen_xml.replace("$SuType_name", "%s-SuType" % sg_obj.name)
        gen_xml = gen_xml.replace("$SvcType_name", sg_obj.svc_type)

        parser = xml.XMLParser(remove_blank_text=True)
        etf = cmwETF(sg_obj)
        etf.etf_xml = xml.XML(gen_xml, parser)
        #sg_xml = xml.XML(gen_xml, parser)
        log.event.debug('Processing ETF for SG: %s' % sg_obj.name)

        for component in sg_obj.comps:
            #pylint: disable=E1103
            parent_item = etf.etf_xml.findall(".//SUType")[0]
            #pylint: enable=E1103
            self.__inject_element(parent_item, "componentType",
                                   attribs={"name": "safCompType=" + \
                                            component.comp_type,
                                            "version": "safVersion=" + \
                                            component.version}
                                  )

            comp_type = comp_type_template.replace("$comp_type_name",
                                          component.comp_type)
            comp_type = comp_type.replace("$comp_type_version",
                                          component.version)
            comp_type = comp_type.replace("$comp_type_provides_cs",
                                          component.cs_type)
            comp_type = comp_type.replace("$start_cmd",
                                          component.start_command)
            comp_type = comp_type.replace("$stop_cmd",
                                          component.stop_command)
            comp_type = comp_type.replace("$status_cmd",
                                          component.status_command)
            comp_type = comp_type.replace("$cleanup_cmd",
                                          component.cleanup_command)
            # Always the first
            bundle_ref = "safSmfBundle=" + sg_obj.bundles[0].name
            comp_type = comp_type.replace("$bundle_reference",
                                          bundle_ref)
            comp_xml = xml.XML(comp_type, parser)
            #pylint: disable=E1103
            etf.etf_xml.append(comp_xml)
            parent_item = etf.etf_xml.findall(".//ServiceType")[0]
            #pylint: enable=E1103
            self.__inject_element(parent_item, "csType",
                                   attribs={"name": "safCSType=" + \
                                            component.cs_type,
                                            "version": "safVersion=" + \
                                            component.version}
                                  )
            self.__inject_csType(etf.etf_xml, component.cs_type, "1.0.0")
            for bundle in sg_obj.bundles:
                self.__inject_swBundle(etf.etf_xml, bundle.name)
            str_xml = xml.tostring(etf.etf_xml, encoding="UTF-8", \
                                            pretty_print=True)
            etf.etf_xml = str_xml
            log.event.debug("The ETF for SG '%s' was created" % sg_obj.name)
            return etf

    @staticmethod
    def update_etf_template(etf_path, cmw_name, provider):
        _etf_content = []
        with open(etf_path, "r") as f:
            _etf_content = f.readlines()

        with open(etf_path, "w") as f:
            for line in _etf_content:
                line = line.replace('$provider', provider)
                line = line.replace('$name', cmw_name)
                f.write(line)

    def __inject_element(self, parent_item, element_name, attribs):
        element = xml.Element(element_name)
        for attr in attribs:
            element.attrib[attr] = attribs[attr]
        parent_item.insert(0, element)

    def __inject_csType(self, gen_xml, CSType, version):
        """
        :summary : creates a CSType element for a component of the form :
        <AmfEntityType>
            <CSType name="safCSType=App2-CSType" version="safVersion=1.0.0" />
        </AmfEntityType>
        """
        amf_entity = xml.Element("AmfEntityType")
        element = xml.Element("CSType")
        element.attrib["name"] = "safCSType=" + CSType
        element.attrib["version"] = "safVersion=" + version
        amf_entity.append(element)
        gen_xml.append(amf_entity)

    def __inject_swBundle(self, gen_xml, bundle_name):
        '''
        :summary: creates swbundle element and children
        '''
        # Check if name already exists
        for bundle in gen_xml.findall(".//swBundle"):
            if bundle.attrib["name"] == "safSmfBundle=" + bundle_name:
                return None

        element = xml.fromstring(cmw_constants.SW_BUNDLE_ETF_TEMPLATE)
        element.attrib["name"] = "safSmfBundle=" + bundle_name
        gen_xml.append(element)
