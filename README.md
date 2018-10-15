pys4ext
=======

A collection of command-line tools to manage extension sources

* [slicer_extensions_index_checkout.py](slicer_extensions_index_checkout.py): Download and update extension source checkouts
associated with extension description files.


Motivations
-----------

Provide a simple interface to download extensions sources without relying on the more complex extensions index
build system.

Usage
-----

```
cd ~/Projects
git clone git://github.com/Slicer/ExtensionsIndex.git
git clone git://github.com/jcfr/ps4ext.git
mkvirtualenv pys4ext
cd pys4ext
pip install -r requirements.txt
./slicer_extensions_index_checkout.py ../ExtensionsIndex ../ExtensionsSource
```

Glossary
--------

* extension description file: It is a text file with `*.s4ext` extension allowing to specify metadata
associated with a Slicer extension. See [spec][slicer-extension-description-file-spec] for complete list
of metadata.

* extensions index:  It is a repository containing a list of extension description files *.s4ext. These
files are used by the Slicer extensions build system to build, test, package and upload extensions on the
extensions server. See https://github.com/Slicer/ExtensionsIndex/

[slicer-extension-description-file-spec]: http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Developers/Extensions/DescriptionFile
