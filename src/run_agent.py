import subprocess


if __name__ == "__main__":
	p = subprocess.Popen(["sudo", "python" ,"agent_backup2.py"], stdin = subprocess.PIPE, stdout = subprocess.PIPE ,stderr = subprocess.PIPE, shell =False)
	print p.stdout.read()
	print p.stderr.read()
	#p.communicate()
