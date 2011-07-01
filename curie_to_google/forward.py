import getpass
import imaplib
import sys

def cpimap(user1, host1, pass1, user2, host2, pass2):
    m1 = imaplib.IMAP4_SSL(host1, 993)
    m2 = imaplib.IMAP4_SSL(host2, 993)
    m1.login(user1, pass1)
    m2.login(user2, pass2)

    print 'Copying', f
    m1.select('INBOX')
    m2.select('Inbox')
    print 'Fetching messages...'
    typ, data = m1.search(None, 'UNREAD')
    msgs = data[0].split()
    sys.stdout.write(" ".join(['Copying', str(len(msgs)), 'messages']))
    for num in msgs:
        typ, data = m1.fetch(num, '(RFC822)')
        sys.stdout.write('%s' % num)
        m2.append(f, None, None, data[0][1])
        sys.stdout.write('\n')

h1 = 'mail.curie.fr'
u1 = 'tjones'
pass1 = getpass.getpass('PW curie: ')
h2 = 'imap.gmail.com'
u2 = 'thouis'
pass2 = getpass.getpass('PW google: ')

cpimap(u1, h2, pass1, u2, h2, pass2)
