from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.stats_manager import StatsManager
from scenedetect import open_video
from scenedetect.detectors.content_detector import ContentDetector
from scenedetect import save_images
from utils import FILE_PATH

def find_scenes(video_path: str):
    video_manager = VideoManager([video_path])
    stats_manager = StatsManager()
    scene_manager = SceneManager(stats_manager)

    # 使用contect-detector
    scene_manager.add_detector(ContentDetector(threshold=50))

    try:
        video_manager.set_downscale_factor()

        video_manager.start()

        scene_manager.detect_scenes(frame_source=video_manager)

        scene_list = scene_manager.get_scene_list()
                                          
        print('List of scenes obtained:')
        for i, scene in enumerate(scene_list):
            print(
                'Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
                    i + 1,
                    scene[0].get_timecode(), scene[0].get_frames(),
                    scene[1].get_timecode(), scene[1].get_frames(),))

    finally:
        video_manager.release()

def cut_videos(video_path):
    from scenedetect import detect, ContentDetector, split_video_ffmpeg
    scene_list = detect(video_path, ContentDetector(threshold=50))
    split_video_ffmpeg(video_path, scene_list, output_dir=FILE_PATH + 'videos/videos_cut/')

def cut_pic(video_path: str, out_path: str, num_images: int) -> None:
    """
    视频切分镜头然后每个镜头平均取num_images数量的帧，存入文件夹中

    Args:
        video_path: 输出的视频地址
        out_path: 输出图片的地址
        num_images: 输出图片的数量
    """
    # 
    # video_manager = VideoManager([video_path])
    # stats_manager = StatsManager()
    # scene_manager = SceneManager(stats_manager)

    # # 使用contect-detector
    # scene_manager.add_detector(ContentDetector(threshold=27))
    # video_manager.set_downscale_factor()
    # video_manager.start()
    # scene_manager.detect_scenes(frame_source=video_manager)
    # scene_list = scene_manager.get_scene_list()

    video_manager = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=27))
    scene_manager.detect_scenes(video_manager)
    scene_list = scene_manager.get_scene_list()

    save_images(scene_list=scene_list, video=video_manager, num_images=num_images, output_dir=out_path)

if __name__ == '__main__':
    video_path = FILE_PATH + 'videos/374798.mp4'
    out_path = FILE_PATH + 'pics/374798/'
    # find_scenes('build_labels/videos/a.mp4')
    # cut_videos(video_path)
    cut_pic(video_path, out_path, 4)
