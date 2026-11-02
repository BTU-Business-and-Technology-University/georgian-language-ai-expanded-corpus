> **Independent audit revision 2.0.3-full-checked:** All original data and export behavior are preserved. No reduced training selection is applied. See [current independent findings and limitations](INDEPENDENT_AUDIT_ka.md). Original claims below are not independently verified unless the audit explicitly confirms them.

# GitHub-ზე ატვირთვა — v2.0.1

ZIP-ის გაშლისას მიიღება ერთი რეპოზიტორიისთვის მომზადებული საქაღალდე. რეპოზიტორიაში ატვირთეთ მისი შიგთავსი: მონაცემების ნაწილები, აღწერები, კოდი, მაგალითები და ანგარიშები. ფაილების რაოდენობის გამო მოსახერხებელია GitHub Desktop ან Git.

მთლიანი, დაახლოებით 418 MB-იანი ZIP გამოიყენეთ GitHub Release-ის ჩამოსატვირთ დანართად. რეპოზიტორიაში მისი შიგთავსი განათავსეთ; მთელი ZIP ჩვეულებრივ Git ფაილად არ დაამატოთ. მონაცემები 339 მცირე ნაწილადაა დაყოფილი და თითოეული 25 MiB-ზე ნაკლებია. Release-ის ვერსიაა `v2.0.1`.

```bash
python -m pip install -r requirements.txt
python scripts/verify_distribution.py .
python scripts/test_release_checks.py .
```

სრული გადამოწმება, დროისა და საკმარისი მეხსიერების არსებობისას:

```bash
python scripts/audit_release.py .
python scripts/audit_support.py .
```

აუდიტი გაუშვით ჩვეულებრივი Python-ით, `-O`-ს და `PYTHONOPTIMIZE`-ის გარეშე. საწყის მასალებთან ხელახალი რვასიტყვიანი შედარება დამატებით მოითხოვს კერძო, ავტორიზებულ წყაროს ინდექსს; ის საჯარო პაკეტში არ შედის. მოწოდებულ ანგარიშში ეს სრული შედარება შესრულებულია.

საჯარო აღწერისთვის გამოიყენეთ დაახლოებით 150 მილიონი ქართული სასწავლო ტოკენი და მიუთითეთ სინთეზური წარმოშობა. [PUBLIC_RELEASE_ka.md](PUBLIC_RELEASE_ka.md) დაწერილია გამოქვეყნებული რელიზის ფორმით და გასაშვებია GitHub-ზე რეალური ატვირთვის შემდეგ.

ოფიციალური წესები: [დიდი ფაილები](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), [Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases). წესები გადამოწმდა 2026-10-26. ამ დავალების ფარგლებში GitHub-ზე გამოქვეყნება არ შესრულებულა.
