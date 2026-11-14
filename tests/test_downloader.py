import os
import sys
import unittest

from playlistDownloader import (
    sanitize_filename,
    normalize_youtube_url,
    detect_environment,
    normalize_download_directory,
    get_default_download_directory,
)


class TestPlaylistDownloader(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Queen: Bohemian Rhapsody?"), "Queen_ Bohemian Rhapsody_")
        self.assertEqual(sanitize_filename('Test / Path \\ Name * "Special" <Tag> | Test?'), 'Test _ Path _ Name _ _Special_ _Tag_ _ Test_')
        self.assertEqual(sanitize_filename("   ...Song Title...  "), "Song Title")
        self.assertEqual(sanitize_filename(""), "Unknown_Title")

    def test_normalize_youtube_mix_url(self):
        url = "https://www.youtube.com/watch?v=-8OsZxDZCgg&list=RD-8OsZxDZCgg&start_radio=1"
        res = normalize_youtube_url(url)
        self.assertEqual(res['type'], 'mix')
        self.assertEqual(res['list_id'], 'RD-8OsZxDZCgg')
        self.assertEqual(res['video_id'], '-8OsZxDZCgg')
        self.assertFalse(res['is_private'])
        self.assertEqual(res['clean_url'], "https://www.youtube.com/watch?v=-8OsZxDZCgg&list=RD-8OsZxDZCgg")

    def test_normalize_youtube_playlist_url(self):
        url = "https://www.youtube.com/playlist?list=PLrAlbmPo5Ymp30Kq122r4R6b_R4sD2qVz"
        res = normalize_youtube_url(url)
        self.assertEqual(res['type'], 'playlist')
        self.assertEqual(res['list_id'], 'PLrAlbmPo5Ymp30Kq122r4R6b_R4sD2qVz')
        self.assertFalse(res['is_private'])

    def test_normalize_liked_videos_url(self):
        url = "https://www.youtube.com/watch?v=65A7_eNDcks&list=LL"
        res = normalize_youtube_url(url)
        self.assertEqual(res['type'], 'playlist')
        self.assertEqual(res['list_id'], 'LL')
        self.assertEqual(res['video_id'], '65A7_eNDcks')
        self.assertTrue(res['is_private'])

    def test_normalize_single_video_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        res = normalize_youtube_url(url)
        self.assertEqual(res['type'], 'video')
        self.assertEqual(res['video_id'], 'dQw4w9WgXcQ')
        self.assertEqual(res['clean_url'], "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_detect_environment(self):
        env = detect_environment()
        self.assertIn('system', env)
        self.assertIn('machine', env)
        self.assertIn('description', env)
        self.assertIsInstance(env['is_termux'], bool)
        self.assertIsInstance(env['is_android'], bool)

    def test_normalize_download_directory_scoped_storage(self):
        scoped_path = "/storage/emulated/0/Android/media/com.termux/Music"
        clean = normalize_download_directory(scoped_path)
        self.assertEqual(clean, "/storage/emulated/0/Music")

        scoped_path_2 = "/storage/shared/Android/media/com.termux"
        clean_2 = normalize_download_directory(scoped_path_2)
        self.assertEqual(clean_2, "/storage/shared/Music")


if __name__ == '__main__':
    unittest.main()
