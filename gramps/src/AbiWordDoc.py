#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import os
import base64

from TextDoc import *
from latin_utf8 import latin_to_utf8
import const
import string
import utils
cnv = utils.fl2txt

try:
    import PIL.Image
    no_pil = 0
except:
    no_pil = 1


class AbiWordDoc(TextDoc):

    def __init__(self,styles,type,orientation):
        TextDoc.__init__(self,styles,type,orientation)
        self.f = None
        self.level = 0
        self.new_page = 0

    def open(self,filename):

        if filename[-4:] != ".abw":
            self.filename = "%s.abw" % filename
        else:
            self.filename = filename

        self.f = open(self.filename,"w")
        self.f.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
        self.f.write('<abiword version="0.7.14" fileformat="1.0">\n')
        self.f.write('<pagesize ')
        self.f.write('pagetype="%s" ' % self.paper.get_name())
        if self.orientation == PAPER_PORTRAIT:
            self.f.write('orientation="portrait" ')
        else:
            self.f.write('orientation="landscape" ')
        self.f.write('width="%s" ' % cnv("%.4f",self.width/2.54))
        self.f.write('height="%s" ' % cnv("%.4f",self.height/2.54))
        self.f.write('units="inch" page-scale="1.000000"/>\n')
        self.f.write('<section ')
        rmargin = float(self.rmargin)/2.54
        lmargin = float(self.lmargin)/2.54
        self.f.write('props="page-margin-right:%sin; ' % \
                     cnv("%.4f",rmargin))
        self.f.write('page-margin-left:%sin"' % \
                     cnv("%.4f",lmargin))
        self.f.write('>\n')

    def close(self):
        self.f.write('</section>\n')
        if len(self.photo_list) > 0:
            self.f.write('<data>\n')
            for file_tuple in self.photo_list:
                file = file_tuple[0]
                width = file_tuple[1]
                height = file_tuple[2]
                base = "/tmp/%s.png" % os.path.basename(file)
                tag = string.replace(base,'.','_')

                if no_pil:
                    cmd = "%s -geometry %dx%d '%s' '%s'" % (const.convert,width,height,file,base)
                    os.system(cmd)
                else:
                    im = PIL.Image.open(file)
                    im.thumbnail((width,height))
                    im.save(base,"PNG")

                self.f.write('<d name="')
                self.f.write(tag)
                self.f.write('" mime-type="image/png" base64="yes">\n')
                f = open(base,"rb")
                base64.encode(f,self.f)
                f.close()
                os.unlink(base)
                self.f.write('</d>\n')
            self.f.write('</data>\n')

        self.f.write('</abiword>\n')
        self.f.close()

    def add_photo(self,name,x,y):
        import GdkImlib

        image = GdkImlib.Image(name)
        scale = float(image.rgb_width)/float(image.rgb_height)
        act_width = x * scale
        act_height = y * scale

        self.photo_list.append((name,act_width*40,act_height*40))

	base = "/tmp/%s.png" % os.path.basename(name)
        tag = string.replace(base,'.','_')

        self.f.write('<image dataid="')
        self.f.write(tag)
        width = cnv("%.3f",act_width)
        height = cnv("%.3f",act_height)
        self.f.write('" props="width:%sin; ' % width)
        self.f.write('height:%sin"/>'  % height)

    def start_paragraph(self,style_name,leader=None):
        style = self.style_list[style_name]
        self.current_style = style
        self.f.write('<p props="')
        if style.get_alignment() == PARA_ALIGN_RIGHT:
            self.f.write('text-align:right;')
        elif style.get_alignment() == PARA_ALIGN_LEFT:
            self.f.write('text-align:left;')
        elif style.get_alignment() == PARA_ALIGN_CENTER:
            self.f.write('text-align:center;')
        else:
            self.f.write('text-align:justify;')
        rmargin = cnv("%.4f",float(style.get_right_margin())/2.54)
        lmargin = cnv("%.4f",float(style.get_left_margin())/2.54)
        indent = cnv("%.4f",float(style.get_first_indent())/2.54)
        self.f.write(' margin-right:%sin;' % rmargin)
        self.f.write(' margin-left:%sin;' % lmargin)
        self.f.write(' tabstops:%sin/L;' % lmargin)
        self.f.write(' text-indent:%sin' % indent)
        self.f.write('">')
        font = style.get_font()
        self.f.write('<c props="font-family:')
        if font.get_type_face() == FONT_SANS_SERIF:
            self.f.write('Arial;')
        else:
            self.f.write('Times New Roman;')
        self.f.write('font-size:%dpt' % font.get_size())
        if font.get_bold():
            self.f.write('; font-weight:bold')
        if font.get_italic():
            self.f.write('; font-style:italic')
        color = font.get_color()
        if color != (0,0,0):
            self.f.write('; color:%2x%2x%2x' % color)
        if font.get_underline():
            self.f.write('; text-decoration:underline')
        self.f.write('">')
        if self.new_page == 1:
            self.new_page = 0
            self.f.write('<pbr/>')
        if leader != None:
            self.f.write(leader)
            self.f.write('\t')
                     
    def page_break(self):
        self.new_page = 1

    def end_paragraph(self):
        self.f.write('</c></p>\n')

    def write_text(self,text):
	self.f.write(text)

    def start_bold(self):
        font = self.current_style.get_font()
        self.f.write('</c><c props="font-family:')
        if font.get_type_face() == FONT_SANS_SERIF:
            self.f.write('Arial;')
        else:
            self.f.write('Times New Roman;')
        self.f.write('font-size:%dpt' % font.get_size())
        self.f.write('; font-weight:bold')
        if font.get_italic():
            self.f.write('; font-style:italic')
        color = font.get_color()
        if color != (0,0,0):
            self.f.write('; color:%2x%2x%2x' % color)
        if font.get_underline():
            self.f.write('; text-decoration:underline')
        self.f.write('">')

    def end_bold(self):
        font = self.current_style.get_font()
        self.f.write('</c><c props="font-family:')
        if font.get_type_face() == FONT_SANS_SERIF:
            self.f.write('Arial;')
        else:
            self.f.write('Times New Roman;')
        self.f.write('font-size:%dpt' % font.get_size())
        if font.get_bold():
            self.f.write('; font-weight:bold')
        if font.get_italic():
            self.f.write('; font-style:italic')
        color = font.get_color()
        if color != (0,0,0):
            self.f.write('; color:%2x%2x%2x' % color)
        if font.get_underline():
            self.f.write('; text-decoration:underline')
        self.f.write('">')

    
