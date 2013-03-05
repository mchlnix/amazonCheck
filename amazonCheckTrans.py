#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from colors import GREEN, RED

strings = {
#amazonCheck.py
'dashes'    : '---------------------------------------',
'show-head' : '\tPrice\tMin\tAvg\tMax\tTitle\t',                                                              #Watch the indents!
'add-artcl' : 'Adding article from: ',                                                                        #Url #Log
'add-succs' : 'Article successfully deleted',
'artcl-skp' : '    Article was skipped: ',                                                                    #Url #Spaces #Log+
'ch-mx-slp' : 'Changed MAX_SLEEP_TIME to ',                                                                   #Seconds #Log+
'ch-mn-slp' : 'Changed MIN_SLEEP_TIME to ',                                                                   #Seconds #Log+
'ch-silent' : 'Changed output-mode to SILENT',                                                                #Log+
'ch-updonl' : 'Changed output-mode to UPDATES_ONLY',                                                          #Log+
'ch-verbos' : 'Changed output-mode to VERBOSE',                                                               #Log+
'con-tmout' : '  Connection timed out. ',                                                                     #Spaces #Log+
'no-conect' : 'Could not connect to website. Please check the provided link or your internet connection.',    #Exit message
'dat-fl-ms' : 'Data File does not exist.',                                                                    #Exit #Log+
'dat-fl-rd' : 'Data File is being read',                                                                      #Log
'data-prcs' : 'Data is being processed',                                                                      #Log
'del-mn-cl' : 'Delete Menu called',                                                                           #Log
'opt-types' : 'Did not write to Config File. Options did not match necessary types',                          #Log+
'err-gener' : 'Encountered error',                                                                            #Json and UTF8 problem
'err-rd-cf' : 'Error reading configurations from config file.',                                               #Log
'err-conec' : 'Error while connecting',                                                                       #Log+
'err-con-s' : '  Error while connecting',                                                                     #Spaces #Log+
'exit-norm' : 'Exited normally',                                                                              #Log+
'getng-dat' : '  Getting data',                                                                               #Spaces #Log+
'mxslp-nan' : 'Given max_sleep argument was not a number',                                                    #Log+
'mnslp-nan' : 'Given min_sleep argument was not a number',                                                    #Log+
'ill-argmt' : 'Illegal argument detected: ',                                                                  #Argument #Log+
'it-took'   : '  It took ',                                                                                   #Seconds #Log+
'bec-avail' : 'Just became ' + GREEN + 'available',                                                           #Notif
'bec-unava' : 'Just became ' + RED + 'not available',                                                         #Notif
'N/A'       : 'N/A',
'del-selct' : 'Please select the item to delete ( 0 to exit ): ',                                             #delete menu
'price-dwn' : 'Price went ' + GREEN + 'down ( ',                                                              #Notif #Brace
'price-up'  : 'Price went ' + RED + 'up ( ',                                                                  #Notif #Brace
'prgm-clld' : 'Program called with',                                                                          #Argument #Log
'prgm-hltd' : 'Program halted',                                                                               #Log+
'pg-hlt-ad' : 'Program halted after adding article',                                                          #Log
'pg-hlt-op' : 'Program halted after output',                                                                  #Log
'pg-hlt-us' : 'Program halted by user',                                                                       #Log+
'prgm-term' : 'Program is terminating',                                                                       #Log+
'indx-nofd' : 'Provided index was not found.',
'rd-cf-fil' : 'Read from Config File at ',                                                                    #Log
'rs-cf-fil' : 'Reset Config File at ',                                                                        #Log
'svng-data' : 'Saving data',                                                                                  #Spaces, #Log+
'seconds'   : ' seconds',                                                                                     #Spaces #Log+
'slctn-nan' : 'Selection not an Integer',                                                                     #Log
'slctn-nir' : 'Selection not in range of article list',                                                       #Log
'sh-del-mn' : 'Showing delete menu',                                                                          #Log
'sh-hlp-mn' : 'Showing help-text',                                                                            #Log
'sh-art-ls' : 'Showing list',                                                                                 #Log
'sleep-for' : '  Sleeping for ',                                                                              #Seconds, #Log+
'str-mn-lp' : 'Starting main loop',                                                                           #Log
'str-prgm'  : 'Started Program',                                                                              #Log
'strtg-run' : 'Starting run ',                                                                                #Number #Log+
'wrt-cf-fl' : 'Wrote to Config File at ',                                                                     #Log
'input-nan' : 'Your input was not interpreted.',                                                              #NaN
#amazonCheckLib.py
'date-frmt' : '[%d.%m.%y - %H:%M:%S]',                                                                        #Date Format
'help-add'  : 'add "amazon_link"        adds an article to the list',                                         #add_link #helptext
'help-del'  : 'delete                   shows the delete menu',                                               #delete_menu #helptext
'help-show' : 'show                     shows an overview of all articles',                                   #show_artcls #helptext
'help-help' : 'help, -h, --help         displays this help text',                                             #show_help #helptext
'help-slnt' : '-s, --silent             runs in the background completely silent',                            #silent_mode #helptext
'help-upon' : '-u, --updates_only       shows notification bubbles, otherwise silent',                        #updates_only_mode #helptext
'help-verb' : '-v, --verbose            mirrors the logfile to the commandline',                              #verbose_mode #helptext
'help-mnsl' : '--min_sleep=1234         sets the min. time between updates to 1234s',                         #min_time #helptext
'help-mxsl' : '--max_sleep=1234         sets the max. time between updates to 1234s',                         #max_time #helptext
}
