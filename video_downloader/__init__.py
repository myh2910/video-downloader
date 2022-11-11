import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer

import requests

HOME = "Video"

def wget(url, path, session=requests, err_format="%s", max_repeat=3):
	_err = ""
	while max_repeat > 0:
		try:
			res = session.get(url)
			res.raise_for_status()
			with open(path, "wb") as file:
				file.write(res.content)
			return True
		except Exception as err:
			_err = err
		max_repeat -= 1
	print(err_format % _err)
	return False

def get_fragment(task):
	fragment, path, session, idx = task
	print(f" [{idx}] Connecting to {fragment}...")
	return wget(fragment, path, session, f" [{idx}] %s")

def download_playlist(
	title,
	url,
	dirname="1080p",
	ext="mp4",
	max_duration=None,
	max_workers=10,
	subtitle=None
):
	elapsed_time = -default_timer()

	if not os.path.exists(f"{HOME}/{title}/{dirname}/"):
		os.makedirs(f"{HOME}/{title}/{dirname}/")
	fragment_path = f"{HOME}/{title}/{dirname}/%d.ts"
	output_path = f"{HOME}/{title}/{title}.{ext}"

	try:
		res = requests.get(url)
		res.raise_for_status()

		content = res.content.decode("utf8") + "\n"
		fragments = [requests.compat.urljoin(url, _url) for _url in re.findall(",\n(.*?)\n", content)]
		num_fragments = len(fragments)
		print(":: %d fragments found, downloading..." % num_fragments)

		with requests.Session() as session:
			tasks = []
			for i, fragment in enumerate(fragments):
				if not os.path.exists(fragment_path % i):
					tasks.append((fragment, fragment_path % i, session, f"{i + 1}/{num_fragments}"))
					continue

			with ThreadPoolExecutor(max_workers) as pool:
				pool.map(get_fragment, tasks)

		if max_duration:
			with requests.Session() as session:
				tasks = []
				for i, fragment in enumerate(fragments):
					result = subprocess.run([
							"ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", fragment_path % i
						],
						stdout=subprocess.PIPE,
						stderr=subprocess.STDOUT
					)
					duration = result.stdout.decode("utf8").split("\r")[0]
					print(f" [{i + 1}/{num_fragments}] Fragment duration: {duration}")
					if duration != "N/A" and float(duration) < max_duration:
						os.remove(fragment_path % i)
						tasks.append((fragment, fragment_path % i, session, f"{i + 1}/{num_fragments}"))

				with ThreadPoolExecutor(max_workers) as pool:
					pool.map(get_fragment, tasks)

		with open(output_path, "wb") as video:
			for i in range(num_fragments):
				if not os.path.exists(fragment_path % i):
					print(f" File {fragment_path % i} doesn't exist")
					break

				print(f" [{i + 1}/{num_fragments}] Merging fragment {fragment_path % i}...")
				with open(fragment_path % i, "rb") as file:
					video.write(file.read())

	except Exception as err:
		print(f" Error: {err}")

	if subtitle:
		print(f" Downloading subtitle {subtitle[0]}...")
		wget(subtitle[0], f"{HOME}/{title}/{title}.{subtitle[1]}")

	elapsed_time += default_timer()
	print(f":: Elapsed time: {elapsed_time:0.2f}")

	return output_path

def download_movie(
	title,
	video_args,
	audio_args,
	ext="mp4",
	max_workers=10,
	subtitle=None
):
	elapsed_time = -default_timer()

	video_path = download_playlist(title, *video_args, max_workers=max_workers)
	audio_path = download_playlist(title, *audio_args, max_workers=max_workers)
	output_path = f"{HOME}/{title}/{title}.{ext}"

	print(" Merging video and audio...")
	os.system(f'ffmpeg -i "{video_path}" -i "{audio_path}" -c copy "{output_path}"')

	if subtitle:
		print(f" Downloading subtitle {subtitle[0]}...")
		wget(subtitle[0], f"{HOME}/{title}/{title}.{subtitle[1]}")

	elapsed_time += default_timer()
	print(f":: Elapsed time: {elapsed_time:0.2f}")

	return output_path

def download(
	title,
	url,
	dirname="1080p",
	ext="mp4",
	subtitle=None
):
	elapsed_time = -default_timer()

	if not os.path.exists(f"{HOME}/{title}/{dirname}/"):
		os.makedirs(f"{HOME}/{title}/{dirname}/")
	fragment_path = f"{HOME}/{title}/{dirname}/%d.ts"
	output_path = f"{HOME}/{title}/{title}.{ext}"

	try:
		print(":: Downloading...")

		i = 0
		while True:
			status = get_fragment((url % i, fragment_path % i, requests, str(i + 1)))
			if not status:
				break
			i += 1

		num_fragments = i

		with open(output_path, "wb") as video:
			for i in range(num_fragments):
				if not os.path.exists(fragment_path % i):
					print(f" File {fragment_path % i} doesn't exist")
					break

				print(f" [{i + 1}/{num_fragments}] Merging fragment {fragment_path % i}...")
				with open(fragment_path % i, "rb") as file:
					video.write(file.read())

	except Exception as err:
		print(f" Error: {err}")

	if subtitle:
		print(f" Downloading subtitle {subtitle[0]}...")
		wget(subtitle[0], f"{HOME}/{title}/{title}.{subtitle[1]}")

	elapsed_time += default_timer()
	print(f":: Elapsed time: {elapsed_time:0.2f}")

	return output_path
