#!/usr/bin/env python

import argparse
import os
import sys
import glob


def __predictions_set_to_sorted_list(predictions):
    '''
    :param predictions: set(['leu(80.0)', 'val(80.0)', 'hpg(60.0)', 'ile(90.0)'])
    :return: 'ile(90.0);leu(80.0);val(80.0);hpg(60.0)'
    '''
    return ';'.join(sorted(list(predictions), key=lambda x: (-float(x.split('(')[1].split(')')[0]), x.split('(')[0])))


def __print_msg(msg, exit=False, compared_fpaths=None):
    if compared_fpaths is not None:
        msg = 'Comparing files %s AND %s: ' % (os.path.basename(compared_fpaths[0]),
                                               os.path.basename(compared_fpaths[1])) \
              + msg
    print(msg)
    if exit:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Tester of the antiSMASH v5 converter: compares its output '
                                                 '(ctg*_nrpspredictor2_codes.txt files) to original antiSMASH v3 files')
    parser.add_argument(
        '-1', '--converter-out',
        metavar='FILE/DIR',
        type=str,
        default=None,
        required=True,
        help='ctg*_nrpspredictor2_codes.txt file or the entire "nrpspks_predictions_txt" dir generated by the converter'
    )
    parser.add_argument(
        '-2', '--original-out',
        metavar='FILE/DIR',
        type=str,
        default=None,
        required=True,
        help='ctg*_nrpspredictor2_codes.txt file or the entire "nrpspks_predictions_txt" dir generated by antiSMASH v3'
    )
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop processing on the first error.'
    )
    parser.add_argument(
        '--stop-on-mismatch',
        action='store_true',
        help='Stop processing on the first mismatch.'
    )
    parser.add_argument(
        '--allow-skipping',
        action='store_true',
        help='Try to skip original line if a crucial mismatch is detected.'
    )
    parser.add_argument(
        '--type',
        choices=['codes', 'svm'],
        default='codes',
        help='Checking mode ("codes" or "svm" files), default: "%(default)s"'
    )

    args = parser.parse_args()

    if not os.path.exists(args.converter_out) or not os.path.exists(args.original_out):
        print("Error! At least one of the input paths does not exist!")
        sys.exit(1)

    converter_fpaths = []
    original_fpaths = []
    for args_out, fpaths in [(args.converter_out, converter_fpaths), (args.original_out, original_fpaths)]:
        if os.path.isfile(args_out):
            fpaths.append(args_out)
        elif os.path.isdir(args_out):
            basedir = args_out
            if os.path.isdir(os.path.join(basedir, 'nrpspks_predictions_txt')):
                basedir = os.path.join(basedir, 'nrpspks_predictions_txt')
            fpaths += glob.glob(os.path.join(basedir, 'ctg*_nrpspredictor2_%s.txt' % args.type))
        else:
            print("Error! args_out is neither a file nor a dir!")
            sys.exit(1)

    if len(converter_fpaths) != len(original_fpaths) and (len(converter_fpaths) == 0 or len(original_fpaths) == 0):
        print("Error! Number of input paths (ctg*_nrpspredictor2_codes/svm.txt) specified via either -1 or -2 is zero!")
        sys.exit(1)

    converter_fnames = set(map(os.path.basename, converter_fpaths))
    original_fnames = set(map(os.path.basename, original_fpaths))
    if converter_fnames != original_fnames:
        converter_basedir = os.path.dirname(converter_fpaths[0])
        original_basedir = os.path.dirname(original_fpaths[0])
        extra_converter_fnames_str = " ".join(sorted(list(converter_fnames - original_fnames)))
        extra_original_fnames_str = " ".join(sorted(list(original_fnames - converter_fnames)))

        __print_msg("Error! Basenames of input paths (ctg*_nrpspredictor2_codes/svm.txt) do not match in -1 and -2!\n"
                    "\tExtra filenames in converted (basedir: %s): %s\n"
                    "\t\tvs\n"
                    "\tExtra filenames in original (basedir: %s): %s" %
                    (converter_basedir, extra_converter_fnames_str,
                     original_basedir, extra_original_fnames_str), exit=args.stop_on_error)
        common_fnames = converter_fnames & original_fnames
        __print_msg("Note: will proceed with the common set of filenames (len = %d)" % len(common_fnames))
        converter_fpaths = list(map(lambda x: os.path.join(converter_basedir, x), sorted(list(common_fnames))))
        original_fpaths = list(map(lambda x: os.path.join(original_basedir, x), sorted(list(common_fnames))))

    num_global_issues = 0
    for converter_fpath, original_fpath in zip(converter_fpaths, original_fpaths):
        num_local_issues = 0
        num_skipped_lines = 0
        print("Starting analysis for files %s and %s" % (converter_fpath, original_fpath))
        with open(converter_fpath) as converter_f:
            with open(original_fpath) as original_f:
                idx = 0
                external_loop_break = False
                for idx, converter_line in enumerate(converter_f):
                    while True:
                        original_line = original_f.readline()
                        if not original_line:
                            __print_msg("Error! Original file is shorter than the converted one "
                                        "(failed to read line #%d)" % (idx + 1), exit=args.stop_on_error)
                            num_local_issues += 1
                            external_loop_break = True
                            break

                        if args.type == 'codes':
                            conv_label, conv_top1, conv_list = converter_line.split('\t')
                            orig_label, orig_top1, orig_list = original_line.split('\t')
                            if conv_label.split('_')[0] != orig_label.split('_')[0] \
                                    or conv_label.split('_')[-1] != orig_label.split('_')[-1]:
                                __print_msg("Mismatch! Line #%d: labels do not match (%s vs %s)" % (idx + 1, conv_label, orig_label))
                                num_local_issues += 1
                            if conv_top1 != orig_top1:
                                __print_msg("Mismatch (light)! Line #%d: TOP1s do not match (%s vs %s)" % (idx + 1, conv_top1, orig_top1))
                                # num_local_issues += 1 (it is not a real problem if the next check (lists) passes fine
                            conv_set = set(conv_list.strip().split(';'))
                            orig_set = set(orig_list.strip().split(';'))
                            if len(conv_set ^ orig_set):  # symmetric_difference: new set with elements in either s or t but not both
                                __print_msg(
                                    "Mismatch (crucial)! Line #%d: LISTs do not match:\n"
                                    "\tExtra elements in converted: %s\n"
                                    "\t\tvs\n"
                                    "\tExtra elements in original: %s" % (idx + 1,
                                                                          __predictions_set_to_sorted_list(conv_set - orig_set),
                                                                          __predictions_set_to_sorted_list(orig_set - conv_set)),
                                exit=args.stop_on_mismatch)
                                num_local_issues += 1
                                if args.allow_skipping:
                                    print('Warn: trying to skip line #%d in the original file' % (idx + num_skipped_lines))
                                    num_skipped_lines += 1
                                    continue
                        elif args.type == 'svm':
                            if converter_line.startswith('#'):
                                if converter_line != original_line:
                                    __print_msg("Error! Headers do not match, skipping checking of the rest!",
                                                exit=args.stop_on_error)
                                    num_local_issues += 1
                                    external_loop_break = True
                                break

                            conv_label = converter_line.split('\t')[0]
                            orig_label = original_line.split('\t')[0]
                            if conv_label.split('_')[0] != orig_label.split('_')[0] \
                                    or conv_label.split('_')[-1] != orig_label.split('_')[-1]:
                                __print_msg("Mismatch! Line #%d: labels do not match (%s vs %s)" % (idx + 1, conv_label, orig_label))
                                num_local_issues += 1

                            conv_key_columns = ' '.join(converter_line.split('\t')[1:7])
                            orig_key_columns = ' '.join(original_line.split('\t')[1:7])
                            if conv_key_columns != orig_key_columns:
                                __print_msg("Mismatch! Line #%d: key columns do not match (%s vs %s)"
                                            % (idx + 1, conv_key_columns, orig_key_columns))
                                num_local_issues += 1
                                if args.allow_skipping:
                                    print('Warn: trying to skip line #%d in the original file' % (idx + num_skipped_lines))
                                    num_skipped_lines += 1
                                    continue
                        break
                    if external_loop_break:
                        break

                original_line = original_f.readline()
                if original_line:
                    __print_msg("Error! Original file is larger than the converted one "
                                "(able to read line AFTER #%d)" % (idx + 1), exit=args.stop_on_error)
                    num_local_issues += 1
        if num_local_issues:
            print("Done! Files %s and %s are NOT equivalent (see %d issues above)\n" %
                  (converter_fpath, original_fpath, num_local_issues))
        else:
            print("Done! Files %s and %s are equivalent\n" % (converter_fpath, original_fpath))
        if num_skipped_lines:
            print("\tNote: %d lines were skipped during the comparison!" % num_skipped_lines)
        num_global_issues += num_local_issues

    if len(converter_fpaths) > 1:
        if num_global_issues:
            print("Done! Dirs %s and %s are NOT equivalent (see %d issues above)" %
                  (args.converter_out, args.original_out, num_global_issues))
        else:
            print("Done! Dirs %s and %s are equivalent" % (args.converter_out, args.original_out))
    if num_global_issues:
        return 1
    return 0

    '''
cat /Users/alex/biolab/nerpa/examples_antismash3/nrpspks_predictions/GCA_000716815.1/nrpspks_predictions_txt/ctg17_nrpspredictor2_codes.txt 
ctg17_orf00004_A1	ser	ser(100.0);arg(60.0);glu(60.0);ala(60.0);gln(50.0);hpg(50.0);trp(50.0);thr(50.0);pro(50.0);cys(50.0);phe(50.0);leu(50.0);asp(50.0);orn(50.0);b-ala(50.0);dab(50.0);gly(50.0);asn(40.0);tyr(40.0);dht(40.0);bht(40.0);lys(40.0);val(40.0);bmt(40.0);ala-d(40.0);cit(40.0);dpg(40.0);ahp(40.0);met(40.0);uda(40.0);hse(40.0);apa(40.0);cha(40.0);allothr(40.0);apc(40.0);dhpg(30.0);vol(30.0);dhp(30.0);pip(30.0);abu(30.0);end(30.0);ile(30.0);phg(30.0);aad(30.0);aeo(30.0);hyv(30.0);hty(30.0);his(30.0);dhb(20.0);tcl(20.0);gua(20.0);sal(10.0)
ctg17_orf00004_A2	ile	ile(90.0);leu(80.0);val(80.0);hpg(60.0);tyr(60.0);glu(50.0);gly(50.0);gln(50.0);bht(50.0);dhpg(50.0);dhp(50.0);abu(50.0);dpg(50.0);ala(50.0);asp(50.0);phe(50.0);pip(50.0);met(50.0);hse(50.0);orn(50.0);cys(40.0);trp(40.0);thr(40.0);asn(40.0);dht(40.0);pro(40.0);lys(40.0);ser(40.0);bmt(40.0);end(40.0);phg(40.0);arg(40.0);hty(40.0);apa(40.0);cha(40.0);allothr(40.0);vol(30.0);ala-d(30.0);cit(30.0);aad(30.0);ahp(30.0);uda(30.0);gua(30.0);sal(20.0);dhb(20.0);tcl(20.0);dab(20.0);aeo(20.0);hyv(20.0);his(20.0);apc(20.0);b-ala(10.0)
ctg17_orf00006_A1	gln	gln(70.0);phe(60.0);val(60.0);ser(50.0);ala(50.0);abu(50.0);glu(50.0);uda(50.0);leu(50.0);orn(40.0);gly(40.0);trp(40.0);arg(40.0);tyr(40.0);thr(40.0);bht(40.0);dhpg(40.0);asp(40.0);dpg(40.0);dhp(40.0);bmt(40.0);cys(40.0);dab(40.0);lys(40.0);pro(30.0);asn(30.0);ile(30.0);dht(30.0);hpg(30.0);vol(30.0);pip(30.0);ala-d(30.0);cit(30.0);end(30.0);aeo(30.0);hty(30.0);his(30.0);allothr(30.0);sal(20.0);phg(20.0);aad(20.0);hyv(20.0);ahp(20.0);met(20.0);b-ala(20.0);hse(20.0);apa(20.0);gua(20.0);cha(20.0);apc(20.0);dhb(10.0);tcl(10.0)
ctg17_orf00006_A2	ahp	ahp(60.0);ser(50.0);dab(50.0);orn(50.0);apa(50.0);pro(40.0);leu(40.0);arg(40.0);val(40.0);cys(40.0);trp(40.0);ala(40.0);vol(40.0);lys(40.0);cit(40.0);end(40.0);met(40.0);his(40.0);hse(40.0);phe(40.0);gly(40.0);apc(40.0);tyr(30.0);asn(30.0);glu(30.0);hpg(30.0);asp(30.0);thr(30.0);gln(30.0);dht(30.0);bht(30.0);ile(30.0);pip(30.0);bmt(30.0);ala-d(30.0);aeo(30.0);hty(30.0);uda(30.0);cha(30.0);allothr(30.0);dhb(20.0);dhpg(20.0);dpg(20.0);dhp(20.0);abu(20.0);phg(20.0);aad(20.0);b-ala(20.0);gua(20.0);sal(10.0);tcl(10.0);hyv(10.0)

cat /Users/alex/biolab/nerpa/examples_antismash5/TEST_OUT1/ctg17_nrpspredictor2_codes.txt
ctg17_orf00003_A1	ser	ser(100.0);ala(60.0);arg(60.0);glu(60.0);asp(50.0);cys(50.0);gln(50.0);gly(50.0);leu(50.0);phe(50.0);pro(50.0);thr(50.0);trp(50.0);b-ala(50.0);orn(50.0);dab(50.0);hpg(50.0);ala-d(40.0);asn(40.0);lys(40.0);met(40.0);allothr(40.0);tyr(40.0);val(40.0);dpg(40.0);dht(40.0);bht(40.0);bmt(40.0);hse(40.0);apa(40.0);apc(40.0);cit(40.0);uda(40.0);cha(40.0);ahp(40.0);his(30.0);ile(30.0);aad(30.0);abu(30.0);pip(30.0);dhpg(30.0);dhp(30.0);aeo(30.0);phg(30.0);vol(30.0);hyv(30.0);hty(30.0);end(30.0);xxx(30.0);dhb(20.0);tcl(20.0);gua(20.0);sal(10.0)
ctg17_orf00003_A2	ile	ile(90.0);leu(80.0);val(80.0);tyr(60.0);hpg(60.0);ala(50.0);asp(50.0);gln(50.0);glu(50.0);gly(50.0);met(50.0);phe(50.0);orn(50.0);abu(50.0);pip(50.0);dhpg(50.0);dhp(50.0);dpg(50.0);bht(50.0);hse(50.0);arg(40.0);asn(40.0);cys(40.0);lys(40.0);pro(40.0);ser(40.0);thr(40.0);allothr(40.0);trp(40.0);dht(40.0);phg(40.0);bmt(40.0);hty(40.0);apa(40.0);end(40.0);cha(40.0);ala-d(30.0);aad(30.0);vol(30.0);gua(30.0);cit(30.0);uda(30.0);ahp(30.0);his(20.0);dab(20.0);dhb(20.0);sal(20.0);aeo(20.0);tcl(20.0);hyv(20.0);apc(20.0);b-ala(10.0);xxx(10.0)
ctg17_orf00004_A1	gln	gln(70.0);phe(60.0);val(60.0);ala(50.0);glu(50.0);leu(50.0);ser(50.0);abu(50.0);uda(50.0);arg(40.0);asp(40.0);cys(40.0);gly(40.0);lys(40.0);thr(40.0);trp(40.0);tyr(40.0);orn(40.0);dab(40.0);dhpg(40.0);dhp(40.0);dpg(40.0);bht(40.0);bmt(40.0);ala-d(30.0);asn(30.0);his(30.0);ile(30.0);pro(30.0);allothr(30.0);pip(30.0);hpg(30.0);dht(30.0);aeo(30.0);vol(30.0);hty(30.0);cit(30.0);end(30.0);met(20.0);b-ala(20.0);aad(20.0);sal(20.0);phg(20.0);hyv(20.0);hse(20.0);apa(20.0);apc(20.0);gua(20.0);cha(20.0);ahp(20.0);xxx(20.0);dhb(10.0);tcl(10.0)
ctg17_orf00004_A2	ahp	ahp(60.0);ser(50.0);orn(50.0);dab(50.0);apa(50.0);ala(40.0);arg(40.0);cys(40.0);gly(40.0);his(40.0);leu(40.0);lys(40.0);met(40.0);phe(40.0);pro(40.0);trp(40.0);val(40.0);vol(40.0);hse(40.0);apc(40.0);cit(40.0);end(40.0);ala-d(30.0);asn(30.0);asp(30.0);gln(30.0);glu(30.0);ile(30.0);thr(30.0);allothr(30.0);tyr(30.0);pip(30.0);hpg(30.0);dht(30.0);bht(30.0);aeo(30.0);bmt(30.0);hty(30.0);uda(30.0);cha(30.0);b-ala(20.0);aad(20.0);abu(20.0);dhb(20.0);dhpg(20.0);dhp(20.0);dpg(20.0);phg(20.0);gua(20.0);xxx(20.0);sal(10.0);tcl(10.0);hyv(10.0)
    '''


if __name__ == "__main__":
    main()
