#!/usr/bin/env python3

"""==================================================================================================
#  Script to check if a domain name has HTTP(s) Traffic.
#  I use it during pen-testing after Sublist3r!
#  Martin Thodi 2018 (martthodi238@gmail.com)
=================================================================================================="""

import requests, argparse, signal, multiprocessing


def usage():
    parser = argparse.ArgumentParser(description="Checks domain name for HTTP(s)")
    parser.add_argument("infile", help="File with domain list")
    parser.add_argument("-p", metavar="processes", help="# of processes (default 8)")
    parser.add_argument("-o", metavar="Output file", help="Output filename (default codes_results.csv and results.txt)")
    return parser.parse_args()


def main():
    global args; args = usage()
    try:
        # read the domain names
        domains = [line.rstrip() for line in open(args.infile)]
        # set the number of processes to spawn
        pses = min(abs(int(args.p or 8)), len(domains)) or 1
        output_name = args.o or "results"
    except (IOError, ValueError) as e: print(e); return
    # exit on ctrl-c
    sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    # check domains in parallel
    pool = multiprocessing.Pool(processes=pses)
    signal.signal(signal.SIGINT, sigint_handler)
    try:
        # lock = multiprocessing.Lock()
        result = pool.map(test_http, domains)
        print("[i]Saving results to file....")
        write_to_file(result, output_name)
        print("[i]Results saved to : codes_" + output_name + ".csv and " + output_name+".txt" )

    except KeyboardInterrupt :
        pass


def write_to_file(results_list, output_file):
    """ Saves the results to files.
        @:arg results_list - a list domains from worker pools
        @:arg output_file - well output file
    """
    if len(results_list) > 0:
        try:
            status_code_file_handle = open('codes_' + output_file + '.csv', 'a')
            no_status_code_file_handle = open(output_file+'.txt', 'a')
            for domain in results_list:
                if domain is not None:
                    write_with_codes(domain, status_code_file_handle)
                    write_without_codes(domain[1], no_status_code_file_handle)
        except IOError as e:
            print(e.strerror)
        finally:
            status_code_file_handle.close()
            no_status_code_file_handle.close()


def write_with_codes(code_domain_list, file_handle):
    """ @:arg code_domain_list : [status_code, domain_name]"""
    if code_domain_list is not None:
        file_handle.write(str(code_domain_list[0]) + "," + code_domain_list[1] + "\n")


def write_without_codes(domain, file_handle):
    """@:arg domain : domain name"""
    if domain is not None:
        file_handle.write(domain + "\n")


def test_http(domain):
    # user-agent, more headers for requests can be added here
    headers = {'user-agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36' }
    print("[i]checking : " + domain)
    # check  http
    try:
        r = requests.get('http://' + domain, headers=headers, allow_redirects=False)
        if r.status_code == 301 or r.status_code == 302 or r.status_code == 307:  # requires HTTPS?
            try:
                r2 = requests.get('https://' + domain, headers=headers, allow_redirects=False)
                if r2.status_code == 301 or r.status_code == 302 or r.status_code == 307:  # needs www?
                    try:
                        r3 = requests.get('https://www.' + domain, headers=headers, allow_redirects=False)
                        if r3.status_code != 404: # everything else is interesting
                            return [r3.status_code , 'https://www.' + domain]
                    except Exception as e:
                        print("[!!]Error connecting to : " + domain + " Nothing unusual. We are handle it.")
                if r2.status_code != 404:
                    return [r2.status_code , 'https://' + domain]
            except Exception as e:
                print("[!!]Error connecting to : " + domain + " Nothing unusual. We are handling it.")
                #return None
        if r.status_code != 404:
            return [r.status_code, 'http://' + domain]
    #  Some requests might get stuck retrying on http when all we need is https
    except Exception as e:
        try :
            r3 = requests.get('https://www.' + domain, headers=headers, allow_redirects=False)
            # print(r3.status_code)
            if r3.status_code != 404:
                return [r3.status_code, 'https://www.' + domain]
        except Exception as e:
            print("[!!]Error connecting to : " + domain + " Nothing unusual. We are handling it.")


if __name__ == '__main__':
    main()