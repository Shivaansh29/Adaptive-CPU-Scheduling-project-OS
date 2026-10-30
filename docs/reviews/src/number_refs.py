"""Build review3.html from review3_keys.html.

Citations are written as [@key] in review3_keys.html. This script numbers them
in order of first appearance, replaces them with [n] and writes the reference
list in that order. Run from anywhere:  python3 docs/reviews/src/number_refs.py
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFS = {
    'silb': "A. Silberschatz, P. B. Galvin, and G. Gagne, <i>Operating System Concepts</i>, 10th ed. Hoboken, NJ, USA: Wiley, 2018, ch. 5.",
    'purohit': "M. Purohit, Z. Svitkina, and R. Kumar, &ldquo;Improving online algorithms via ML predictions,&rdquo; in <i>Advances in Neural Information Processing Systems 31 (NeurIPS)</i>, 2018.",
    'mitzsurvey': "M. Mitzenmacher and S. Vassilvitskii, &ldquo;Algorithms with predictions,&rdquo; in <i>Beyond the Worst-Case Analysis of Algorithms</i>, T. Roughgarden, Ed. Cambridge, U.K.: Cambridge University Press, 2021, ch. 30, pp. 646\u2013662.",
    'mitzitcs': "M. Mitzenmacher, &ldquo;Scheduling with predictions and the price of misprediction,&rdquo; in <i>Proc. 11th Innovations in Theoretical Computer Science Conf. (ITCS)</i>, LIPIcs vol. 151, 2020, pp. 14:1&ndash;14:18.",
    'rai': "I. A. Rai, G. Urvoy-Keller, and E. W. Biersack, &ldquo;Analysis of LAS scheduling for job size distributions with high variance,&rdquo; in <i>Proc. ACM SIGMETRICS</i>, San Diego, CA, USA, 2003, pp. 218&ndash;228.",
    'jain': "R. Jain, D. Chiu, and W. Hawe, &ldquo;A quantitative measure of fairness and discrimination for resource allocation in shared computer systems,&rdquo; Digital Equipment Corporation, Tech. Rep. DEC-TR-301, 1984.",
    'efron': "B. Efron and R. J. Tibshirani, <i>An Introduction to the Bootstrap</i>. Monographs on Statistics and Applied Probability, vol. 57. New York, NY, USA: Chapman &amp; Hall, 1993.",
    'wilcoxon': "F. Wilcoxon, &ldquo;Individual comparisons by ranking methods,&rdquo; <i>Biometrics Bulletin</i>, vol. 1, no. 6, pp. 80&ndash;83, 1945.",
    'holm': "S. Holm, &ldquo;A simple sequentially rejective multiple test procedure,&rdquo; <i>Scandinavian Journal of Statistics</i>, vol. 6, no. 2, pp. 65&ndash;70, 1979.",
    'friedman': "J. H. Friedman, &ldquo;Greedy function approximation: A gradient boosting machine,&rdquo; <i>Annals of Statistics</i>, vol. 29, no. 5, pp. 1189&ndash;1232, 2001.",
    'sklearn': "F. Pedregosa <i>et al.</i>, &ldquo;Scikit-learn: Machine learning in Python,&rdquo; <i>Journal of Machine Learning Research</i>, vol. 12, pp. 2825&ndash;2830, 2011.",
    'ostep': "R. H. Arpaci-Dusseau and A. C. Arpaci-Dusseau, <i>Operating Systems: Three Easy Pieces</i>, v1.00. Arpaci-Dusseau Books, 2018, chs. 7&ndash;8.",
    'corbato': "F. J. Corbat&oacute;, M. Merwin-Daggett, and R. C. Daley, &ldquo;An experimental time-sharing system,&rdquo; in <i>Proc. Spring Joint Computer Conf. (AFIPS)</i>, 1962, pp. 335&ndash;344.",
    'matarneh': "R. J. Matarneh, &ldquo;Self-adjustment time quantum in round robin algorithm depending on burst time of the now running processes,&rdquo; <i>American Journal of Applied Sciences</i>, vol. 6, no. 10, pp. 1831&ndash;1837, 2009.",
    'noon': "A. Noon, A. Kalakech, and S. Kadry, &ldquo;A new round robin based scheduling algorithm for operating systems: Dynamic quantum using the mean average,&rdquo; <i>International Journal of Computer Science Issues</i>, vol. 8, no. 3, pp. 224&ndash;229, 2011.",
    'pbdrr': "R. Mohanty, H. S. Behera, K. Patwari, M. Dash, and M. L. Prasanna, &ldquo;Priority based dynamic round robin (PBDRR) algorithm with intelligent time slice for soft real time systems,&rdquo; <i>International Journal of Advanced Computer Science and Applications</i>, vol. 2, no. 2, pp. 46&ndash;50, 2011.",
    'negi': "A. Negi and P. K. Kumar, &ldquo;Applying machine learning techniques to improve Linux process scheduling,&rdquo; in <i>Proc. IEEE Region 10 Conference (TENCON)</i>, 2005, pp. 1&ndash;6.",
    'pourali': "A. Pourali and A. M. Rahmani, &ldquo;A fuzzy-based scheduling algorithm for prediction of next CPU-burst time to implement shortest process next,&rdquo; in <i>Proc. IACSIT Spring Conference (IACSIT-SC)</i>, 2009, pp. 217&ndash;220.",
    'helmy': "T. Helmy and A. Dekdouk, &ldquo;Burst round robin as a proportional-share scheduling algorithm,&rdquo; in <i>Proc. IEEE GCC Conference</i>, 2007.",
    'lottery': "C. A. Waldspurger and W. E. Weihl, &ldquo;Lottery scheduling: Flexible proportional-share resource management,&rdquo; in <i>Proc. 1st USENIX Symp. Operating Systems Design and Implementation (OSDI)</i>, 1994, pp. 1&ndash;11.",
    'smith': "W. Smith, I. Foster, and V. Taylor, &ldquo;Predicting application run times using historical information,&rdquo; in <i>Job Scheduling Strategies for Parallel Processing</i>, LNCS vol. 1459. Springer, 1998, pp. 122&ndash;142.",
    'tsafrir': "D. Tsafrir, Y. Etsion, and D. G. Feitelson, &ldquo;Backfilling using system-generated predictions rather than user runtime estimates,&rdquo; <i>IEEE Transactions on Parallel and Distributed Systems</i>, vol. 18, no. 6, pp. 789&ndash;803, 2007.",
    'mao16': "H. Mao, M. Alizadeh, I. Menache, and S. Kandula, &ldquo;Resource management with deep reinforcement learning,&rdquo; in <i>Proc. 15th ACM Workshop on Hot Topics in Networks (HotNets)</i>, 2016, pp. 50&ndash;56.",
    'mao19': "H. Mao, M. Schwarzkopf, S. B. Venkatakrishnan, Z. Meng, and M. Alizadeh, &ldquo;Learning scheduling algorithms for data processing clusters,&rdquo; in <i>Proc. ACM SIGCOMM</i>, 2019, pp. 270&ndash;288.",
    'kahu': "S. Y. Kahu, &ldquo;KernelOracle: Predicting the Linux scheduler's next move with deep learning,&rdquo; arXiv:2505.15213, 2025.",
    'zhang': "Y. Zhang, X. Zhao, Z. Li, G. Cheng, J. Yin, L. Zhang, and Z. Chen, &ldquo;Integrating artificial intelligence into operating systems: A survey on techniques, applications, and future directions,&rdquo; arXiv:2407.14567, 2024.",
    'cfs': "Linux Kernel Documentation, &ldquo;CFS Scheduler.&rdquo; [Online]. Available: https://docs.kernel.org/scheduler/sched-design-CFS.html",
    'xv6': "R. Cox, M. F. Kaashoek, and R. Morris, <i>xv6: A Simple, Unix-like Teaching Operating System</i>. MIT, 2020.",
}


def main():
    src = (HERE / "review3_keys.html").read_text()
    body = src.split("<h2>References</h2>")[0]
    order = []
    for key in re.findall(r"\[@(\w+)\]", body):
        if key not in order:
            order.append(key)
    missing = [k for k in order if k not in REFS]
    if missing:
        raise SystemExit(f"unknown citation keys: {missing}")
    num = {k: i + 1 for i, k in enumerate(order)}
    out = re.sub(r"\[@(\w+)\]", lambda m: f"[{num[m.group(1)]}]", src)
    out = out.replace("@REFERENCES@", "\n".join(f"<p>[{num[k]}] {REFS[k]}</p>" for k in order))
    (HERE / "review3.html").write_text(out)
    unused = [k for k in REFS if k not in num]
    print(f"review3.html: {len(order)} references" + (f"; unused: {unused}" if unused else ""))


if __name__ == "__main__":
    main()
