import os
import re
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer

import requests

from .config import CONFIG

tmp = {}

class Timer:
	def start(self):
		self.elapsed_time = -default_timer()

	def end(self):
		self.elapsed_time += default_timer()
		print(f":: Elapsed time: {self.elapsed_time:0.2f} seconds")

def wget(url, path, session=requests, err_format="%s", headers=None):
	if not headers:
		headers = CONFIG['headers']
	max_repeat = CONFIG['repeat']
	error = ""

	while max_repeat > 0:
		try:
			res = session.get(url, headers=headers)
			res.raise_for_status()
			with open(path, "wb") as file:
				file.write(res.content)
			return True
		except Exception as err:
			error = err
		max_repeat -= 1

	print(err_format % error)
	return False

def get_fragment(task):
	session, key, url, path, idx = task
	print(f" [{idx}] Connecting to {url}...")
	if not wget(url, path, session, f" [{idx}] %s", tmp[key]['headers']):
		tmp[key]['status'] = False

def get_fragments_url(key):
	max_repeat = CONFIG['repeat']
	error = ""

	while max_repeat > 0:
		try:
			res = requests.get(tmp[key]['url'], headers=CONFIG['headers'])
			res.raise_for_status()
			tmp[key]['status'] = True
		except Exception as err:
			error = err
		max_repeat -= 1

	if not tmp[key]['status']:
		print(error)
		return

	tmp[key]['urls'] = [requests.compat.urljoin(tmp[key]['url'], i)
		for i in re.findall(",\n(.*?)\n", res.content.decode("utf8") + "\n")]
	tmp[key]['num'] = len(tmp[key]['urls'])
	tmp[key]['path'] = os.path.join(tmp['path'], key)
	tmp[key]['file'] = os.path.join(tmp[key]['path'], "%d.ts")
	tmp[key]['idx'] = key.upper() + " %d/" + str(tmp[key]['num'])

	if not os.path.exists(tmp[key]['path']):
		os.makedirs(tmp[key]['path'])

	print(f":: [{key.upper()}] {tmp[key]['num']} fragments found.")

def download_video(
	title,
	video_url,
	video_headers=None,
	audio_url=None,
	audio_headers=None,
	subtitle=None,
	subtitle_headers=None
):
	timer = Timer()
	timer.start()

	tmp['path'] = os.path.join(CONFIG['home'], title)
	tmp['output'] = os.path.join(tmp['path'], title + ".%s")

	keys = []
	if video_url:
		keys.append('video')
		tmp['video'] = {
			'url': video_url,
			'headers': video_headers,
			'output': tmp['output'] % CONFIG['exts'][0],
			'status': False
		}
	if audio_url:
		keys.append('audio')
		tmp['audio'] = {
			'url': audio_url,
			'headers': audio_headers,
			'output': tmp['output'] % CONFIG['exts'][1],
			'status': False
		}

	# Get fragments urls
	for key in keys:
		print(f":: Downloading {key}...")
		if os.path.exists(tmp[key]['output']):
			print(f" File {tmp[key]['output']} already exists.")
		else:
			get_fragments_url(key)

	# Download fragments
	with requests.Session() as session:
		tasks = []

		for key in keys:
			if not tmp[key]['status']:
				continue

			for i in range(tmp[key]['num']):
				path = tmp[key]['file'] % i
				idx = tmp[key]['idx'] % (i + 1)

				if os.path.exists(path):
					print(f" [{idx}] File {path} already exists.")
				else:
					tasks.append((session, key, tmp[key]['urls'][i], path, idx))

		with ThreadPoolExecutor(CONFIG['threads']) as pool:
			pool.map(get_fragment, tasks)

	# Merge fragments
	for key in keys:
		if not tmp[key]['status']:
			continue

		print(f":: Merging {key} fragments...")

		with open(tmp[key]['output'], "wb") as output:
			for i in range(tmp[key]['num']):
				path = tmp[key]['file'] % i
				idx = tmp[key]['idx'] % (i + 1)

				if not os.path.exists(path):
					print(f" File {path} doesn't exist.")
					break

				print(f" [{idx}] Merging fragment {path}...")
				with open(path, "rb") as file:
					output.write(file.read())

	# Merge video and audio files
	while video_url and audio_url:
		print(":: Merging video and audio...")

		if os.path.exists(tmp['output'] % CONFIG['exts'][2]):
			print(f" File {tmp['output'] % CONFIG['exts'][2]} already exists.")
			break

		for key in keys:
			if not os.path.exists(tmp[key]['output']):
				print(f" File {tmp[key]['output']} doesn't exist.")
				keys = None
				break

		if keys:
			os.system('ffmpeg -i "%s" -i "%s" -c copy "%s"' % (
				tmp['output'] % CONFIG['exts'][i] for i in range(3)
			))
		break

	# Download subtitle file
	if subtitle:
		print(f":: Downloading subtitle {subtitle[0]}...")
		wget(subtitle[0], tmp['output'] % subtitle[1], headers=subtitle_headers)

	timer.end()
