"""Markdown filters
This file contains a collection of utility filters for dealing with 
markdown within Jinja templates.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import sys
import subprocess
from HTMLParser import HTMLParser

from .html import html2latex
from IPython.nbconvert.utils.pandoc import pandoc

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

__all__ = [
    'markdown2html',
    'markdown2latex',
    'markdown2rst',
    'extended_markdown2latex'
]

def markdown2latex(source):
    """Convert a markdown string to LaTeX via pandoc.

    This function will raise an error if pandoc is not installed.
    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    source : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as returned by pandoc.
    """
    return pandoc(source, 'markdown', 'latex')

def markdown2html(source):
    """Convert a markdown string to HTML via pandoc"""
    return pandoc(source, 'markdown', 'html', extra_args=['--mathjax'])

def markdown2rst(source):
    """Convert a markdown string to LaTeX via pandoc.

    This function will raise an error if pandoc is not installed.
    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    source : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as returned by pandoc.
    """
    return pandoc(source, 'markdown', 'rst')

def extended_markdown2latex(source):
    """Convert a markdown string with html tags to LaTeX via pandoc.

    Splits the string into markdown and html parts. 
    These are converted using the base methods and combined.

    Parameters
    ----------
    source : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as a combination of strings returned by pandoc.
    """
    # instantiate the parser and fed it some HTML
    parser = MarkdownSplitParser()
    parser.feed(source)
    outtext = ''
    for substring in parser.splitlist:
        if substring[0] == 'markdown':
            outtext += markdown2latex(substring[3])
        elif substring[0] == 'html':
            outtext += html2latex(substring[3])
        else:
            # tag type not defined
            pass
    return outtext

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class MarkdownSplitParser(HTMLParser):
    """Markdown Split Parser

    Splits the markdown source into markdown and html parts.
    
    Inherites from HTMLParser, overrides:
     - handle_starttag
     - handle_endtag
     - handle_startendtag
     - handle_data
    """
    opentags = []
    splitlist = []
    setag = False  # .. start-end-tag
    datag = False  # .. data-tag

    def get_offset(self):
        """ Compute startposition in data list """
        lin, offset = self.getpos()
        pos = 0
        for i in range(lin-1):
            pos = self.data.find('\n',pos) + 1
        return pos + offset
        

    def handle_starttag(self, tag, attrs):
        # if image is wrong placed, i.e. not in start-end tag, exclude
        if tag == 'img':
            pass
        else:
            if len(self.opentags)==0:
                pos = self.get_offset()
                if self.datag or self.setag:
                    self.splitlist[-1].append(pos)
                    self.datag = False
                    self.setag = False
                self.splitlist.append(['html',pos])
            self.opentags.append(tag)
    
    def handle_endtag(self, tag):
        self.opentags.pop()
        if len(self.opentags)==0:
            pos = self.get_offset()
            self.splitlist[-1].append(pos+len(tag)+3)
    
    def handle_startendtag(self, tag, attrs):
        """ Parse html start-end tags (<img .../>) """
        if len(self.opentags)==0:
            pos = self.get_offset()
            if self.datag:
                self.splitlist[-1].append(pos)
                self.datag = False
            self.setag = True
            self.splitlist.append(['html',pos])
                
    def handle_data(self, data):
        """ Treat the markdown part """
        if len(self.opentags)==0 and not self.datag:
            pos = self.get_offset()
            if self.setag:
                self.splitlist[-1].append(pos)
                self.setag = False
            self.splitlist.append(['markdown',pos])
            self.datag = True
        
    def feed(self, data):
        self.data = data
        HTMLParser.feed(self,data)
        if len(self.splitlist[-1])==2:
            self.splitlist[-1].append(len(self.data))
        num_pop = 0
        for i,li in enumerate(self.splitlist):
            j = i - num_pop
            self.splitlist[j].append(
                self.data[self.splitlist[j][1]:self.splitlist[j][2]])
            if li[-3] == li[-2]: 
                self.splitlist.pop(i)
                num_pop += 1

