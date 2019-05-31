RAMSES Scene Exporter Blender Add-on
====================================

This add-on is meant to export a [RAMSES](https://github.com/GENIVI/ramses) scene graph right from Blender itself. It is still under development.

RAMSES is a 3D graphics framework concerned with the efficient distribution of graphics among multiple screens for automotive purposes. While the framework is almost complete, it lacks a tool that can load, modify and export 3D assets in a suitable format so applications developed with RAMSES can use them at runtime.

This exporter makes leveraging Blender - a powerful open source 3D modeller - possible for the creation of content to be used in applications developed with the RAMSES framework.

How do I install it?
====================

Build the plugin libraries with CMake, e.g.:
```
$mkdir build && cd build
$cmake -DCMAKE_INSTALL_PREFIX=<path_to_install> ../
$make install
```

Copy the contents of the installation folder to the Blender's add-on directory - it is usually under **version/scripts/addons_contrib**.

For Arch Linux and Blender 2.79, for instance, that would be **/usr/share/blender/2.79/scripts/addons_contrib** assuming you have installed Blender from the official repositories.

Users under Windows should look for a similar folder inside their Blender installation path.

Then, to activate it simply look into **Header Menu > File > User Preferences > Add-ons** (or **Header Menu > Edit > Preferences > Add-ons** if under Blender 2.80) and filter by **Import-Export**.


How do I set up a development environment for contributing?
===========================================================

I recommend building Blender from source and creating a symbolic link from **build_folder/bin/version/scripts/addons_contrib/ramses_scene_exporter** pointing to the directory into which you have cloned this repository. Notice *build_folder* and *version* refer to the directory where you have invoked the build command and the Blender version, respectively.

I recommend using Visual Studio Code with either [this extension](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development) - which simplifies matters greatly, as it facilitates installation, debugging and reloading of code - or at the very least a [debugger extension](https://github.com/AlansCodeLog/blender-debugger-for-vscode).

