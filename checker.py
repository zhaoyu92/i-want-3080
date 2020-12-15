import collections
import os
import random
import signal
import smtplib
import socket
import threading
import time
import urllib2

ContentToCheck = collections.namedtuple('ContentToCheck', ['url', 'content', 'checker', 'v_content', 'v_checker'])

EVGA_CONTENT_TO_CHECK = [
    ContentToCheck('https://www.evga.com/products/product.aspx?pn=10G-P5-3885-KR', 'Out of Stock', lambda x, y: y not in x, 'ADD TO CART', lambda x, y: y in x),
    ContentToCheck('https://www.evga.com/products/product.aspx?pn=10G-P5-3895-KR', 'Out of Stock', lambda x, y: y not in x, 'ADD TO CART', lambda x, y: y in x),
    ContentToCheck('https://www.evga.com/products/product.aspx?pn=10G-P5-3897-KR', 'Out of Stock', lambda x, y: y not in x, 'ADD TO CART', lambda x, y: y in x),
]

NEWEGG_CONTENT_TO_CHECK = [
    ContentToCheck('https://www.newegg.com/p/pl?d=3080+asus', 'Add to cart', lambda x, y: y in x, None, None),
    ContentToCheck('https://www.newegg.com/p/pl?d=3080+evga', 'Add to cart', lambda x, y: y in x, None, None),
]

EMAIL_TEMPLATE = 'Subject: {}\n\n{}'
USER_CREDENTIALS = ('nvidia.3080.buy@gmail.com', 'Johnnyr88590929')
RECEIVERS = ['nvidia.3080.buy@gmail.com']


class ContentChecker(threading.Thread):

  def __init__(self, sleep_left, sleep_right, contents_to_check):
    threading.Thread.__init__(self)

    self._sleep_left = sleep_left
    self._sleep_right = sleep_right
    self._contents_to_check = contents_to_check

    # The shutdown_flag is a threading.Event object that
    # indicates whether the thread should be terminated.
    self.shutdown_flag = threading.Event()
    

  def run(self):
    counter = 0
    while not self.shutdown_flag.is_set():
      counter += 1
      if counter % 10 == 0:
        print(time.strftime('%H:%M:%S', time.localtime()))
      for content_to_check in self._contents_to_check:
        try:
          headers = {'User-Agent': 'Mozilla/5.0'}
          req = urllib2.Request(content_to_check.url, None, headers)
          page = urllib2.urlopen(req).read()
          if len(page) < 100000:
            file_path = os.path.join(os.getcwd(), 'exception_doc')
            with open(file_path, 'w') as f:
              f.write(page)
          if counter % 10 == 0:
            file_path = os.path.join(os.getcwd(), 'debug_doc')
            with open(file_path, 'w') as f:
              f.write(page)
            print('{} has length: {}'.format(content_to_check.url, len(page)))
          if content_to_check.checker(page, content_to_check.content):
            self.send_notification(USER_CREDENTIALS, RECEIVERS, 'Content updated in {}'.format(content_to_check.url), content_to_check.url)
            if content_to_check.v_checker is not None:
              if content_to_check.v_checker(page, content_to_check.v_content):
                print('This was a valid finding.')
        # except (urllib2.HTTPError, urllib2.URLError), e:
        #   send_notification(USER_CREDENTIALS, RECEIVERS, 'Exception caught...')
        except Exception:
          self.send_notification(USER_CREDENTIALS, RECEIVERS, 'Exception caught...', page)
      time.sleep(random.randint(self._sleep_left, self._sleep_right))

  def send_notification(self, sender_credentials, receivers, title, content):
    data = EMAIL_TEMPLATE.format(title, content)
    service = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    service.login(sender_credentials[0], sender_credentials[1])
    service.sendmail(sender_credentials[0], receivers, data)
    service.quit()


class ServiceExit(Exception):
  pass


def service_shutdown(signum, frame):
  print('Caught signal %d' % signum)
  raise ServiceExit


def main():
  ip_address = socket.gethostbyname(socket.gethostname())
  print('Your Computer IP Address is: {}'.format(ip_address))

  # Register the signal handlers
  signal.signal(signal.SIGTERM, service_shutdown)
  signal.signal(signal.SIGINT, service_shutdown)

  # Start the job threads
  try:
    pollers = [ContentChecker(30, 60, EVGA_CONTENT_TO_CHECK)]  # , ContentChecker(30, 60, NEWEGG_CONTENT_TO_CHECK)

    for poller in pollers:
      poller.start()

    # Keep the main thread running, otherwise signals are ignored.
    while True:
      time.sleep(1)

  except ServiceExit:
    # Terminate the running threads.
    # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
    for poller in pollers:
      poller.shutdown_flag.set()
    # Wait for the threads to close...
    print('Terminating...')
    print('Since threads are sleeping, this could take a while...')
    while not all([not poller.is_alive() for poller in pollers]):
      time.sleep(5)
      print('Still waiting for threads to terminate...')
    # Terminate for real
    for poller in pollers:
      poller.join()


def ad_hoc_check(url):
  headers = {'User-Agent': 'Mozilla/5.0'}
  req = urllib2.Request(url, None, headers)
  page = urllib2.urlopen(req).read()
  save_path = os.path.join(os.getcwd(), 'page_gen_ad_hoc')
  with open(save_path, 'w') as f:
    f.write(page)


if __name__ == '__main__':
  # ad_hoc_check('https://www.newegg.com/p/pl?d=2080+asus')
  main()
