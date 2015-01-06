all: init/swift.csh init/swift.sh
	@:

install: 
	@-install -d $(DESTDIR)/usr/sbin
	@install sw2account/sw2account.py $(DESTDIR)/usr/sbin
	@-install -d $(DESTDIR)/etc/profile.d
	@install init/swift.sh $(DESTDIR)/etc/profile.d/swift.sh
	@-install -d $(DESTDIR)/etc/csh/login.d
	@install init/swift.csh $(DESTDIR)/etc/csh/login.d/swift.csh

init/swift.csh:
	@sed 's|@sbindir@|/usr/sbin|' init/swift.csh.in > init/swift.csh
init/swift.sh:
	@sed 's|@sbindir@|/usr/sbin|' init/swift.sh.in > init/swift.sh

clean:
	-rm init/swift.csh init/swift.sh

