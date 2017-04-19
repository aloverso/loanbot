#code copied then modified from http://naelshiab.com/tutorial-send-email-python/
import smtplib
import os


def send_email_to_librarian(patron, question):
	pwd = os.environ['librarianEmailPwd']
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login("olincollegelibrary@gmail.com", pwd)
	msg = '\nHi, this is Loan Wrangler on behalf of {}. {} sent me the following message: "{}". I thought you would be a better resource than me to help them. Thanks! Loan Wrangler'.format(patron, patron, question)
	server.sendmail("olincollegelibrary@gmail.com", "mqlkome@gmail.com", msg)
	server.quit()