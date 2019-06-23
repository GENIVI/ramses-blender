
import unittest
import bpy
import ramses_export.debug_utils
import ramses_export.exporter
import ramses_export.ramses_inspector

class TestRamsesBlenderExporter(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_default_scene_does_not_crash_blender(self):
        exporter = ramses_export.exporter.RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)

    def test_default_scene_viewer_does_not_crash_blender(self):
        exporter = ramses_export.exporter.RamsesBlenderExporter(bpy.data.scenes)
        exporter.extract_from_blender_scene()
        exporter.build_from_extracted_representations()

        for exportable_scene in exporter.get_exportable_scenes():
            inspector = ramses_export.ramses_inspector.RamsesInspector(exportable_scene)
            inspector.load_viewer()

            if not exportable_scene.is_valid():
                validation_report = exportable_scene.get_validation_report()
                raise RuntimeError(validation_report)
