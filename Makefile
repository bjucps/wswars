all: wswars_kit.tar.gz register

register: register.c
	gcc register.c -oregister

wswars_kit.tar.gz: setup.sh warproxy.py
	tar zcf wswars_kit.tar.gz setup.sh warproxy.py wwwroot

clean:
	rm register wswars_kit.tar.gz
	