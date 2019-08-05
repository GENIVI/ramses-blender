RAMSES Scene Exporter Blender Add-on
====================================

This add-on is meant as a way to create content for [RAMSES](https://github.com/GENIVI/ramses) using Blender. It does this by exporting a RAMSES scene graph right from Blender itself. **It is still under development.**

RAMSES is a 3D graphics framework concerned with the efficient distribution of graphics among multiple screens for automotive purposes. While the framework is almost complete, it lacks a tool that can load, modify and export 3D assets in a suitable format so applications developed with RAMSES can use them at runtime.

This exporter makes leveraging Blender - a powerful open source 3D modeller - possible for the creation of content to be used in applications developed with the RAMSES framework.

![Here is how it looks currently](DemoScreenshot.png?raw=true "Here is how it looks like currently")

How does it work?
====================
By iterating over the objects in a Blender scene, an intermediary scene graph representation is built. The IR aims to be a middle ground between the abstractions exposed in Blender and in RAMSES. A RAMSES scene graph is then built from this by calling into a set of Python bindings written in C++11/[pybind11](https://github.com/pybind/pybind11) and maintained in a separate repository. These bindings are compiled beforehand into a shared library that gets loaded at runtime by Blender's own Python interpreter. After some validation, a RAMSES scene/resources file is saved and can then be loaded by code built for the RAMSES Framework.

What works, currently?
====================
As of now only meshes and their transformations - scalings, rotations and translations - and modifiers get exported.

What does not work yet?
====================
Materials do not work yet. We are investigating our options on this. It will probably use a combination of [baking](https://docs.blender.org/manual/en/latest/render/blender_render/bake.html) and manual shader editing. It may someday leverage Blender's new 'uber' shader - [Principled BSDF](https://docs.blender.org/manual/en/latest/render/cycles/nodes/types/shaders/principled.html) - to exchange materials with RAMSES.

Also curves, surfaces, metas and text are not supported yet. You can check Blender's object types [here](https://docs.blender.org/manual/en/latest/editors/3dview/object/types.html), but we do not plan on necessarily supporting all of them.

How do I install it?
====================
As of now, you cannot install this directly from Blender itself. This project also requires building the Python bindings for RAMSES, which is referenced as a submodule. Luckily, we provide a CMake script to simplify the installation process.


Build the plugin libraries with CMake, e.g.:
```
$mkdir build && cd build
$cmake -DCMAKE_INSTALL_PREFIX=<path_to_install> -DBLENDER_ADDONS_PATH=<path_to_blender_addons_directory> ..
$make install
```
Make sure you have the dependencies installed. RAMSES lists its dependencies in its own [README](https://github.com/GENIVI/ramses/blob/master/README.md), as does the [Python bindings](https://github.com/GENIVI/ramses-python/).

You need to specify Blender's add-on directory - it is usually under **version/scripts/addons_contrib**.

For Arch Linux and Blender 2.79, for instance, that would be **/usr/share/blender/2.79/scripts/addons_contrib** assuming you have installed Blender from the official repositories.

Users under Windows should look for a similar folder inside their Blender installation path.

After running ```make install``` activate it via **Header Menu > File > User Preferences > Add-ons** (or **Header Menu > Edit > Preferences > Add-ons** if under Blender 2.80). You can filter by **Import-Export** to make it easier to find.


How do I set up a development environment for contributing?
===========================================================

Using vscode:
------------

I recommend using Visual Studio Code with [this extension](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development). Then to install execute the following command: ```>Blender: build and start```. This copies your work into the config folder for Blender - i.e. ```~/.config/blender``` under Linux, which makes the addon available in the Add-ons panel (see above). You still need to activate it though. Debugging should work out of the box.

Using other IDEs/editors:
-------------------------
Install the addon using CMake. You will have setup a debugger yourself. See [this](https://code.blender.org/2015/10/debugging-python-code-with-pycharm/) for more details.

How do I run the tests?
=======================
This project includes both unit and end-to-end tests. You can run the tests with ```python test/run_all_tests.py -b <path_to_your_blender_binary> -p <platform> -a <addon_path>```.

When in doubt, run ```python test/run_all_tests.py --help``` for guidance. Note that ```<addon_path>```  is the full path to where the exporter was installed.

Some tests are vanilla unit tests built with Python's ```unittest``` module, while others check the screenshot of the exported scene against a valid image to determine correctness. This project already includes a list of screenshots of exported scenes that were manually checked to be free of errors, but these can be updated with the ```-g``` flag in the event something major is changed within the exporter  - e.g. when we start supporting materials in the future, these will need to be updated and this is the quickest way to do so.

You can add more tests by appending to the test array in test/run_all_tests.py, and you can add more flags to the tests by reading the instructions in ```run_all_tests.py```.

How do I debug a test?
======================
Run ```python -m pdb test/run_all_tests.py``` and set up a breakpoint in ```p.communicate()```. Alternatively, check out ```stdout.txt, stderr.txt``` and ```debug.txt``` in ```test/test_results/<your_test_name>```
