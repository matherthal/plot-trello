import datetime
import argparse
import logging.config
import configparser
# from notification.simple_email_service import SimpleEmailService


def get_script_arguments():
    args = argparse.ArgumentParser()

    args.add_argument('--environment', '-e', required=True, 
        help='Environment to use (prod or dev)')
    
    args.add_argument('--config-file', '-cf', required=False, 
        help='Path where the script configuration file resides')

    args.add_argument('--log-config-file', '-lcf', required=False, 
        help='Path where the log configuration file resides')

    # args.add_argument('--send-status-email', required=False, default=False, 
    #     action='store_true',
    #     help='Should send status emails or not (error emails are always sent)')

    return vars(args.parse_args())


def create_logger(log_config_file, log_file):
    logging.config.fileConfig(log_config_file)
    my_logger = logging.getLogger(__name__)
    fh = logging.handlers.TimedRotatingFileHandler(log_file, 'midnight')

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    my_logger.addHandler(fh)


def create_config_file(config_file):
    config = configparser.ConfigParser()
    config.readfp(open(config_file))
    return config

# def send_error_email(config, script_name, message=None):

#     ses = SimpleEmailService(config)
#     now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')

#     html_body = """
#     <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
#         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
#     <html xmlns="http://www.w3.org/1999/xhtml">
#     <head>
#     <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
#       <head></head>
#       <body>
#         <h3>Script: %s </h3>
#         <h3>Now: %s</h3>
#         <h3>Message: %s</h3>
#       </body>
#     </html>
#     """ % (script_name, now, message)

#     ses.send_email('Redshift Script Error - ' + script_name, html_body)


# def send_email(config, steps_summary, cluster_summary):

#     ses = SimpleEmailService(config)
#     today = datetime.datetime.now().strftime('%d/%m/%Y')
#     total_time = \
#         int((cluster_summary['end_time'] - cluster_summary['start_time']) / 60)

#     html_body = """
#     <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
#         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
#     <html xmlns="http://www.w3.org/1999/xhtml">
#     <head>
#     <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
#       <head></head>
#       <body>
#         <h1> Day %s</h1>
#         <br>
#         <h3><b>Redshift Scripts Launch Time: %s minutes</b></h3>
#         <table border='1' cellspacing='0' cellpadding='10'>
#             <thead>
#                 <tr>
#                     <th>Steps</th>
#                     <th>Time</th>
#                 </tr>
#             </thead>
#             <tbody align='center'>
#     """ % (today, str(total_time))

#     for summary in steps_summary:
#         html_body += "<tr> " + \
#                         "<td>" + summary['className'] + " </td> " + \
#                         "<td>" + summary['totalTime'] + " s</td> " + \
#                         "</tr>"

#     html_body += " </table> </body> </html> "

#     ses.send_email('Redshift Scripts Launch Status', html_body)
