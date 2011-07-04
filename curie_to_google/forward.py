import getpass
import imaplib
import sys
import time

def cpimap(user1, host1, pass1, user2, host2, pass2):
    m1 = imaplib.IMAP4_SSL(host1, 993)
    m2 = imaplib.IMAP4_SSL(host2, 993)
    m1.login(user1, pass1)
    m2.login(user2, pass2)

    m1.select('INBOX')
    typ, data = m1.search(None, 'UNSEEN')
    msgs = data[0].split()
    print 'Copying', str(len(msgs)), 'messages'
    for ct, num in enumerate(msgs):
        typ, data = m1.fetch(num, '(RFC822)')
        print ct + 1
        m2.append('Inbox', None, None, data[0][1])

h1 = 'mail.curie.fr'
u1 = 'tjones'
pass1 = getpass.getpass('PW curie: ')
h2 = 'imap.gmail.com'
u2 = 'thouis'
pass2 = getpass.getpass('PW google: ')

while True:
    cpimap(u1, h1, pass1, u2, h2, pass2)
    time.sleep(300)
