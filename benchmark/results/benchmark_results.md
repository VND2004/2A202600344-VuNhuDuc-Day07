# Benchmark Report

## Summary

| Strategy | Chunker | Metadata Filter | Chunks | Avg Score |
|---|---|---:|---:|---:|
| markdown_structure_with_filter | DocumentStructureChunker | True | 110 | 0.4403 |
| recursive_with_filter | RecursiveChunker | True | 100 | 0.4374 |
| fixed_baseline | FixedSizeChunker | False | 84 | 0.3720 |
| sentence_basic | SentenceChunker | False | 71 | 0.1985 |

## Query Details

### markdown_structure_with_filter

| Query ID | Keyword | Overlap | Final | Top-1 Artist | Top-1 Preview |
|---|---:|---:|---:|---|---|
| q1 | 0.7500 | 0.3448 | 0.6284 | de_choat | Section: Dế Choắt - Tiểu sử  Anh nổi tiếng với lần dizz Hot Boy Xăm Trổ và trận Beef với Phúc Rey. Năm 2020, anh tham gia chương trình Rap Việt về đội Wowy và gây tiếng vang tại sh |
| q2 | 1.0000 | 0.2469 | 0.7741 | icd | Section: ICD - Tiểu sử  Năm 2020, anh tham gia chương trình King of Rap và trở thành quán quân mùa một của King of Rap.  ICD chơi skill khá tốt và anh được đánh giá khá cao.   " Ng |
| q3 | 0.3333 | 0.1205 | 0.2695 | karik | Section: Karik - Tiểu sử  Gia đình :Trong gia đình Karik có 2 anh em và Karik là con út. Khi đến với nhạc rap Karik bị gia đỉnh phản đối, không được ủng hộ vì anh trai mình là ngườ |
| q4 | 0.3333 | 0.0750 | 0.2558 | wowy | Section: Wowy - Tiểu sử  Wowy tên thật là Nguyễn Ngọc Minh Huy (sinh ngày 27 tháng 9 năm 1988) là một rapper người Việt Nam. Wowy là một rapper "đường phố" được khá nhiều bạn trẻ u |
| q5 | 0.3333 | 0.1351 | 0.2739 | suboi | Section: Suboi - Tiểu sử  "Khi tôi bắt đầu sự nghiệp của mình, không ai thực sự biết 'rap' là gì. Vì thế tôi không biết người Việt Nam sẽ phản ứng như thế nào về nó. Nếu bạn đến Mỹ |

### recursive_with_filter

| Query ID | Keyword | Overlap | Final | Top-1 Artist | Top-1 Preview |
|---|---:|---:|---:|---|---|
| q1 | 0.7500 | 0.3019 | 0.6156 | de_choat | Anh nổi tiếng với lần dizz Hot Boy Xăm Trổ và trận Beef với Phúc Rey. Năm 2020, anh tham gia chương trình Rap Việt về đội Wowy và gây tiếng vang tại show truyền hình này, trở thành |
| q2 | 1.0000 | 0.2564 | 0.7769 | icd | Năm 2020, anh tham gia chương trình King of Rap và trở thành quán quân mùa một của King of Rap.  ICD chơi skill khá tốt và anh được đánh giá khá cao.   " Nghe tao rap dizz mày cảm  |
| q3 | 0.3333 | 0.1250 | 0.2708 | karik | Gia đình :Trong gia đình Karik có 2 anh em và Karik là con út. Khi đến với nhạc rap Karik bị gia đỉnh phản đối, không được ủng hộ vì anh trai mình là người thành công. Nhưng sau kh |
| q4 | 0.3333 | 0.0759 | 0.2561 | wowy | # Wowy - Tiểu sử  Wowy tên thật là Nguyễn Ngọc Minh Huy (sinh ngày 27 tháng 9 năm 1988) là một rapper người Việt Nam. Wowy là một rapper "đường phố" được khá nhiều bạn trẻ undergro |
| q5 | 0.3333 | 0.1143 | 0.2676 | suboi | "Khi tôi bắt đầu sự nghiệp của mình, không ai thực sự biết 'rap' là gì. Vì thế tôi không biết người Việt Nam sẽ phản ứng như thế nào về nó. Nếu bạn đến Mỹ,họ có rất nhiều nhạc rap  |

### fixed_baseline

| Query ID | Keyword | Overlap | Final | Top-1 Artist | Top-1 Preview |
|---|---:|---:|---:|---|---|
| q1 | 0.7500 | 0.0706 | 0.5462 | karik | ủa Việt Nam được giới thiệu với hệ thống CocaCola toàn cầu cùng Music Video “Cứ Là Mình”.  Là gương mặt quảng cáo quen thuộc của những nhãn hàng dành cho giới trẻ năng động : Heine |
| q2 | 1.0000 | 0.2198 | 0.7659 | icd | ply hay diss ICD gồm: Sol'Bass, Dabee, Hale, MC ILL, D Joker,..  Năm 2020, anh tham gia chương trình King of Rap và trở thành quán quân mùa một của King of Rap.  ICD chơi skill khá |
| q3 | 0.3333 | 0.1053 | 0.2649 | karik | Karik bị gia đỉnh phản đối, không được ủng hộ vì anh trai mình là người thành công. Nhưng sau khi Karik là 1 trong 2 nghệ sĩ thắng giải MTV Việt Nam năm 2011 cùng ca sĩ Mỹ Tâm, gia |
| q4 | 0.0000 | 0.0471 | 0.0141 | suboi | ới 14 tuổi và bắt đầu trình diễn rap từ lúc 15 tuổi và sau đó cô nhanh chóng trở thành một trong những rapper nổi tiếng trong giới underground hip hop. Năm 19 tuổi, sau một lần thu |
| q5 | 0.3333 | 0.1176 | 0.2686 | suboi | hạc hip hop từ năm 14 tuổi cũng như bắt đầu trau dồi vốn tiếng Anh của mình bằng việc nghe và rap theo Eminem hay Will Smith. "Khi tôi bắt đầu sự nghiệp của mình, không ai thực sự  |

### sentence_basic

| Query ID | Keyword | Overlap | Final | Top-1 Artist | Top-1 Preview |
|---|---:|---:|---:|---|---|
| q1 | 0.2500 | 0.0777 | 0.1983 | karik | Là gương mặt quảng cáo quen thuộc của những nhãn hàng dành cho giới trẻ năng động : Heineiken,Yomost, VinaGame, Fifa Online. Vào 2018, Karik cùng Orange cho ra bài Người lạ ơi được |
| q2 | 0.3333 | 0.0755 | 0.2560 | minh_lai | Mỗi bài hát của anh đều có một câu chuyện riêng và chứa đựng nhiều thông điệp ý nghĩa. Ngoài rap, anh cũng có nhiều bản ballad nhẹ nhàng, đầy cảm xúc. Anh ta biết cách thể hiện tìn |
| q3 | 0.3333 | 0.1250 | 0.2708 | karik | Gia đình :Trong gia đình Karik có 2 anh em và Karik là con út. Khi đến với nhạc rap Karik bị gia đỉnh phản đối, không được ủng hộ vì anh trai mình là người thành công. Nhưng sau kh |
| q4 | 0.0000 | 0.0533 | 0.0160 | rhymastic | Sau một thời gian tự tìm hiểu về sáng tác và sản xuất sản phẩm âm nhạc từ năm 2009, Rhymastic làm việc tại phòng thu M4ME với các nghệ sĩ như Justa Tee, Young Uno. Với chất giọng t |
| q5 | 0.3333 | 0.0606 | 0.2515 | minh_lai | Mỗi bài hát của anh đều có một câu chuyện riêng và chứa đựng nhiều thông điệp ý nghĩa. Ngoài rap, anh cũng có nhiều bản ballad nhẹ nhàng, đầy cảm xúc. Anh ta biết cách thể hiện tìn |
