# -*- coding: utf-8 -*-
#
# Copyright (C) 2006  Ali Sabil <ali.sabil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

"""SOAP Messages structures."""

import gnet.util.ElementTree as ElementTree
import gnet.util.StringIO as StringIO

__all__=['SOAPRequest', 'SOAPResponse']

class NameSpace:
    SOAP_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"
    SOAP_ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"
    XML_SCHEMA = "http://www.w3.org/1999/XMLSchema"
    XML_SCHEMA_INSTANCE = "http://www.w3.org/1999/XMLSchema-instance"

class Encoding:
    SOAP = "http://schemas.xmlsoap.org/soap/encoding/"

class _SOAPSection:
    ENVELOPE = "{" + NameSpace.SOAP_ENVELOPE + "}Envelope"
    HEADER = "{" + NameSpace.SOAP_ENVELOPE + "}Header"
    BODY = "{" + NameSpace.SOAP_ENVELOPE + "}Body"


class _SOAPElement(object):
    def __init__(self, element):
        self.element = element

    def append(self, tag, namespace=None, attrib={}, value=None, **kwargs):
        if namespace is not None:
            tag = "{" + namespace + "}" + tag
        child = ElementTree.SubElement(self.element, tag, attrib, **kwargs)
        child.text = value
        return _SOAPElement(child)


class SOAPRequest(object):
    """Abstracts a SOAP Request to be sent to the server"""

    def __init__(self, method, namespace=None, encoding_style=Encoding.SOAP):
        """Initializer
        
        @param method: the method to be called
        @type method: string

        @param namespace: the namespace that the method belongs to
        @type namespace: URI
        
        @param encoding_style: the encoding style for this method
        @type encoding: URI"""
        self.header = ElementTree.Element(_SOAPSection.HEADER)
        if namespace is not None:
            method = "{" + namespace + "}" + method
        self.method = ElementTree.Element(method)
        if encoding_style is not None:
            self.method.set("{" + NameSpace.SOAP_ENVELOPE + "}encodingStyle", encoding_style)
    
    def add_argument(self, name, type=None, value=None):
        return self._add_element(self.method, name, type, value)

    def add_header(self, name, namespace=None, value=None):
        if namespace is not None:
            name = "{" + namespace + "}" + name
        return self._add_element(self.header, name, value=value)
    
    def _add_element(self, parent, name, type=None, value=None):
        elem = ElementTree.SubElement(parent, name)
        if type:
            if not isinstance(type, ElementTree.QName):
                type = ElementTree.QName(NameSpace.XML_SCHEMA, type)
            elem.set("{" + NameSpace.XML_SCHEMA_INSTANCE + "}type", type)
        elem.text = value
        return _SOAPElement(elem)
    
    def __str__(self):
        envelope = ElementTree.Element(_SOAPSection.ENVELOPE)
        if len(self.header) > 0:
            envelope.append(self.header)
        body = ElementTree.SubElement(envelope, _SOAPSection.BODY)
        body.append(self.method)
        return "<?xml version=\"1.0\" encoding=\"utf-8\"?>" +\
                ElementTree.tostring(envelope, "utf-8")
    
    def __repr__(self):
        return "<SOAP request %s>" % self.method.tag


class SOAPResponse(object):
    def __init__(self, data):
        self.tree = self._parse(data)
        self.header = self.tree.find(_SOAPSection.HEADER)
        self.body = self.tree.find(_SOAPSection.BODY)

    def _parse(self, data):
        events = ("start", "end", "start-ns", "end-ns")
        ns = []
        data = StringIO.StringIO(data)
        context = ElementTree.iterparse(data, events=events)
        for event, elem in context:
            if event == "start-ns":
                ns.append(elem)
            elif event == "end-ns":
                ns.pop()
            elif event == "start":
                elem.set("(xmlns)", tuple(ns))
        data.close()
        return context.root

