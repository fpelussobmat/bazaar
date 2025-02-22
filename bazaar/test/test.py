import unittest
from bazaar.bazaar import FileSystem
import shutil
import os
import logging

class TestFileSystem(unittest.TestCase):
    def setUp(self):

        tmp_dir = "/tmp/test"
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.mkdir(tmp_dir)
        self.fs = FileSystem(tmp_dir, db_uri="mongodb://localhost/bazaar_test")
        self.fs.db.drop()

    def test_create_file(self):
        content = "This is a test"
        path = "/my_file.txt"
        namespace = "test"
        self.fs.put(path=path, content=content.encode(), namespace=namespace)
        saved_content = self.fs.get(path=path, namespace=namespace).decode()
        self.assertEqual(content, saved_content)

        # Update the file
        self.fs.put(path=path, content="lelelele".encode(), namespace=namespace)
        saved_content = self.fs.get(path=path, namespace=namespace).decode()
        self.assertEqual("lelelele", saved_content)

        # Same file with other namespace
        self.assertIsNone(self.fs.get(path=path, namespace="other"))

    def test_not_exist(self):
        # Same file with other namespace
        self.assertIsNone(self.fs.get(path="/notexists"))

    def test_delete_file(self):
        content = "This is a test"
        path = "/my_file.txt"
        namespace = "test"
        self.fs.put(path=path, content=content.encode(), namespace=namespace)
        self.assertIsNotNone(self.fs.get(path=path, namespace=namespace))
        self.fs.remove(path=path, namespace=namespace)
        self.assertIsNone(self.fs.get(path=path, namespace=namespace))

    def test_list_file(self):
        self.assertEqual([], self.fs.list("/"))
        self.fs.put(path="/first", content="a".encode())
        self.fs.put(path="/dir1/file", content="a".encode())
        self.fs.put(path="/dir1/otherfile", content="a".encode())
        self.assertListEqual(["first"], self.fs.list("/"))
        self.assertListEqual(["file", "otherfile"], self.fs.list("/dir1"))

        # A third level
        self.fs.put(path="/dir1/subdir/prettyfile", content="a".encode())
        self.assertListEqual(["prettyfile"], self.fs.list("/dir1/subdir"))

        # With weird names
        self.fs.put(path="/dir11/./prettyfile", content="a".encode())
        self.assertListEqual(["prettyfile"], self.fs.list("/dir11/."))

        self.fs.put(path="/dir22/$dir/prettyfile", content="a".encode())
        self.assertListEqual(["prettyfile"], self.fs.list("/dir22/$dir"))

    def test_list_file_multilevel(self):
        # multilevel
        self.fs.put(path="/fichero1", content=b"a")
        self.fs.put(path="/dir1/fichero1.1", content=b"a")
        self.fs.put(path="/dir1/fichero1.2", content=b"a")
        self.fs.put(path="/dir2/fichero2.1", content=b"a")
        self.fs.put(path="/dir1/subdir1/a", content=b"a")
        self.fs.put(path="/dir1/subdir1/b", content=b"a")
        self.fs.put(path="/dir1/subdir1/subidr2/c", content=b"a")
        self.fs.put(path="/dir1/subdir2/pepe/cp", content=b"a")
        self.fs.put(path="/this/is/test/file", content=b"a")

        self.assertListEqual(["fichero1"], self.fs.list("/"))
        self.assertListEqual(["fichero1.1", "fichero1.2"], self.fs.list("/dir1"))
        self.assertListEqual(["fichero2.1"], self.fs.list("/dir2"))

        self.assertListEqual(["a", "b"], self.fs.list("/dir1/subdir1"))

        self.assertListEqual(["c"], self.fs.list("/dir1/subdir1/subidr2"))
        self.assertListEqual(["cp"], self.fs.list("/dir1/subdir2/pepe"))
        self.assertListEqual(["file"], self.fs.list("/this/is/test"))

        
    def test_exists(self):
        namespace = "test"
        self.assertFalse(self.fs.exists("/my_file.txt", namespace=namespace))
        content = "This is a test"
        path = "/my_file.txt"
        self.fs.put(path=path, content=content.encode(), namespace=namespace)
        self.assertTrue(self.fs.exists("/my_file.txt", namespace=namespace))
        self.assertFalse(self.fs.exists("/my_file.txt"))

    # Mongomock aggregate does not work
    def test_directories(self):
        self.assertEqual([], self.fs.list("/"))
        self.fs.put(path="/first", content="a".encode())
        self.fs.put(path="/dir1/file", content="a".encode())
        self.fs.put(path="/dir1/secondfile", content="a".encode())
        self.fs.put(path="/dir1/subdir/prettyfile", content="a".encode())
        self.fs.put(path="/dir1/subdir2/prettyfile", content="a".encode())

        self.assertListEqual(["dir1"], self.fs.list_dirs("/"))
        self.assertSetEqual({"subdir", "subdir2"}, set(self.fs.list_dirs("/dir1")))

    def test_directories_multilevel(self):
        # multilevel
        self.fs.put(path="/fichero1", content=b"a")
        self.fs.put(path="/dir1/fichero1.1", content=b"a")
        self.fs.put(path="/dir1/fichero1.2", content=b"a")
        self.fs.put(path="/dir2/fichero2.1", content=b"a")
        self.fs.put(path="/dir1/subdir1/a", content=b"a")
        self.fs.put(path="/dir1/subdir1/b", content=b"a")
        self.fs.put(path="/dir1/subdir1/subidr2/c", content=b"a")
        self.fs.put(path="/dir1/subdir2/pepe/cp", content=b"a")
        self.fs.put(path="/this/is/test/file", content=b"a")

        # assertCountEqual not only counts, is like assertEqual but ignoring the order of the elements in the array
        self.assertCountEqual(["dir1", "dir2", "this"], self.fs.list_dirs("/"))
        self.assertCountEqual(["subdir1", "subdir2"], self.fs.list_dirs("/dir1"))
        self.assertCountEqual([], self.fs.list_dirs("/dir2"))
        self.assertCountEqual(["subidr2"], self.fs.list_dirs("/dir1/subdir1"))
        self.assertCountEqual([], self.fs.list_dirs("/dir1/subdir1/subidr2"))
        self.assertCountEqual(["pepe"], self.fs.list_dirs("/dir1/subdir2"))
        self.assertCountEqual(["test"], self.fs.list_dirs("/this/is"))

    def test_extras(self):
        self.fs.put(path="/first", content="a".encode())
        self.assertEqual({}, self.fs.get_extras(path="/first"))
        self.fs.set_extras(path="/first", extras={"foo": "bar"})
        self.assertEqual({"foo": "bar"}, self.fs.get_extras(path="/first"))


    def test_change_namespace(self):
        namespace = "test_1"
        namespace_2 = "test_2"

        # normal case
        self.fs.put(namespace=namespace, path="/original", content="a".encode())
        self.assertTrue(self.fs.exists(path="/original", namespace=namespace))
        self.assertFalse(self.fs.exists(path="/original", namespace=namespace_2))
        self.assertTrue(self.fs.change_namespace(path="/original", from_namespace=namespace, to_namespace=namespace_2))
        self.assertFalse(self.fs.exists(path="/original", namespace=namespace))
        self.assertTrue(self.fs.exists(path="/original", namespace=namespace_2))

        # wrong cases
        self.assertFalse(self.fs.change_namespace(path="/not_exists", from_namespace=namespace, to_namespace=namespace_2))
        self.fs.put(namespace=namespace, path="/original", content="a".encode())
        self.assertFalse(self.fs.change_namespace(path="/original", from_namespace=namespace, to_namespace=namespace_2))

if __name__ == '__main__':
    unittest.main()
