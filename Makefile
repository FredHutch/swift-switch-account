all: init/swift.csh init/swift.sh init/site-functions/sw2account
	@:

install: 
	@-install -d $(DESTDIR)/usr/sbin
	@install sw2account/sw2account.py $(DESTDIR)/usr/sbin
	@-install -d $(DESTDIR)/etc/profile.d
	@install init/swift.sh $(DESTDIR)/etc/profile.d/swift.sh
	@-install -d $(DESTDIR)/etc/csh/login.d
	@install init/swift.csh $(DESTDIR)/etc/csh/login.d/swift.csh
	@-install -d $(DESTDIR)/usr/local/share/zsh/site-functions
	@install init/site-functions/sw2account \
		$(DESTDIR)/usr/local/share/zsh/site-functions/sw2account

init/swift.csh:
	@sed 's|@sbindir@|/usr/sbin|' init/swift.csh.in > init/swift.csh
init/swift.sh:
	@sed 's|@sbindir@|/usr/sbin|' init/swift.sh.in > init/swift.sh
init/zshenv:
	@sed 's|@sbindir@|/usr/sbin|' init/zshenv.in > init/zshenv
init/site-functions/sw2account:
	@sed 's|@sbindir@|/usr/sbin|' \
		init/site-functions/sw2account.zsh.in > \
		init/site-functions/sw2account

clean:
	-rm init/swift.csh \
		init/swift.sh \
		init/site-functions/sw2account

