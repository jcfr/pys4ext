pys4ext
=======

A command-line tool to download and manage sources associated with extension description files.


Usage
-----

```
cd ~/Projects
git clone git://github.com/Slicer/ExtensionsIndex.git
git clone git://github.com/jcfr/ps4ext.git
mkvirtualenv pys4ext
cd pys4ext
pip install -r requirements.txt
./extensions-index-checkout.py ../ExtensionsIndex ../ExtensionsSource
```

