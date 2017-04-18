#code copied then modified from http://naelshiab.com/tutorial-send-email-python/
import smtplib
patron = "hannah"
question = "how do I use the camera"
def sendEmailToLibrarian(patron, question):
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login("FROM EMAIL", "PASSWORD")
	 
	msg = 'Hi, this is Loan Wrangler on behalf of {}. {} sent me the following message: "{}". I thought you would be a better resource than me to help them. Thanks! Loan Wrangler'.format(patron, patron, question)
	server.sendmail("FROM EMAIL", "TO EMAIL", msg)
	server.quit()

sendEmailToLibrarian(patron, question)
