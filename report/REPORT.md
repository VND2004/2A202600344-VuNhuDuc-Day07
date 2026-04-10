# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Như Đức
**Nhóm:** C401-B6
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity nghĩa là hai vector embedding cùng hướng, nên hai câu có ngữ nghĩa gần nhau dù có thể chứa từ khác nhau. Giá trị càng gần 1 thì mức tương đồng ngữ nghĩa càng cao.

**Ví dụ HIGH similarity:**
- Sentence A: Dế Choắt là quán quân mùa đầu tiên của Rap Việt.
- Sentence B: Nhà vô địch Rap Việt mùa 1 là Dế Choắt.
- Tại sao tương đồng: Cùng nói một fact với cách diễn đạt khác nhau.

**Ví dụ LOW similarity:**
- Sentence A: Suboi từng rap trước Barack Obama tại Việt Nam.
- Sentence B: Tôi thích nấu phở bò vào cuối tuần.
- Tại sao khác: Chủ đề hoàn toàn khác nhau (rap Việt vs thói quen cá nhân).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào hướng vector (ngữ nghĩa) thay vì độ lớn vector, nên ổn định hơn khi độ dài câu khác nhau. Vì vậy nó thường phản ánh mức liên quan ngữ nghĩa tốt hơn Euclidean distance trong bài toán retrieval văn bản.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: số chunks = ceil((doc_length - overlap) / (chunk_size - overlap))
> = ceil((10000 - 50) / (500 - 50))
> = ceil(9950 / 450)
> = ceil(22.11)
> Đáp án: 23 chunks.

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap = 100 thì số chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks, tức tăng từ 23 lên 25. Overlap lớn hơn giúp giữ ngữ cảnh liên tục giữa các chunk, giảm mất ý ở ranh giới chia đoạn.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Tiểu sử và kiến thức chung về rapper Việt Nam

**Tại sao nhóm chọn domain này?**
> Dữ liệu có cấu trúc bán-structured (markdown heading + bảng + đoạn văn), phù hợp để so sánh nhiều chiến lược chunking. Domain này cũng có nhiều fact cụ thể (tên thật, thành tích, chương trình, mốc thời gian) nên dễ thiết kế benchmark query và gold answer. Ngoài ra các câu hỏi có thể kiểm tra rõ hiệu quả của metadata filter theo từng nghệ sĩ.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự (ước tính) | Metadata đã gán |
|---|--------------|-------|---------------------|-----------------|
| 1 | suboi.md | RapViet Wiki | ~3,500 | artist, source, chunk_index, chunker |
| 2 | karik.md | RapViet Wiki | ~3,200 | artist, source, chunk_index, chunker |
| 3 | rhymastic.md | RapViet Wiki | ~3,000 | artist, source, chunk_index, chunker |
| 4 | icd.md | RapViet Wiki | ~4,000 | artist, source, chunk_index, chunker |
| 5 | mc_ill.md | RapViet Wiki | ~3,800 | artist, source, chunk_index, chunker |
| 6 | blacka.md | RapViet Wiki | ~2,500 | artist, source, chunk_index, chunker |
| 7 | young_h.md | RapViet Wiki | ~2,800 | artist, source, chunk_index, chunker |
| 8 | b_ray.md | RapViet Wiki | ~2,600 | artist, source, chunk_index, chunker |
| 9 | de_choat.md | RapViet Wiki | ~3,100 | artist, source, chunk_index, chunker |
| 10 | wowy.md | RapViet Wiki | ~2,900 | artist, source, chunk_index, chunker |
| 11 | minh_lai.md | RapViet Wiki | ~2,400 | artist, source, chunk_index, chunker |
| 12 | phuc_du.md | RapViet Wiki | ~2,700 | artist, source, chunk_index, chunker |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| artist | string | suboi | Filter theo nghệ sĩ để giảm nhiễu và tăng precision |
| source | string | data/raw_data/suboi.md | Trace nguồn, phục vụ kiểm chứng answer |
| chunk_index | int | 4 | Giữ thứ tự chunk để debug và tái dựng ngữ cảnh |
| chunker | string | DocumentStructureChunker | So sánh hiệu quả giữa các strategy |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| de_choat.md | FixedSizeChunker (`fixed_size`) | 3 | 357.0 | Trung bình |
| de_choat.md | SentenceChunker (`by_sentences`) | 3 | 321.3 | Khá tốt |
| de_choat.md | RecursiveChunker (`recursive`) | 3 | 322.3 | Tốt |
| icd.md | FixedSizeChunker (`fixed_size`) | 5 | 423.2 | Trung bình |
| icd.md | SentenceChunker (`by_sentences`) | 3 | 636.7 | Kém ở đoạn dài |
| icd.md | RecursiveChunker (`recursive`) | 6 | 317.8 | Tốt |
| suboi.md | FixedSizeChunker (`fixed_size`) | 12 | 427.2 | Trung bình |
| suboi.md | SentenceChunker (`by_sentences`) | 7 | 651.3 | Kém ở đoạn rất dài |
| suboi.md | RecursiveChunker (`recursive`) | 15 | 303.3 | Tốt |

### Strategy Của Tôi

**Loại:** custom strategy: DocumentStructureChunker + metadata filtering

**Mô tả cách hoạt động:**
> Strategy tách văn bản markdown theo heading trước (regex `^(#{1,6})\s+(.+?)\s*$`), rồi gom nội dung theo từng section để giữ ngữ cảnh chủ đề. Mỗi chunk được thêm prefix `Section: ...` để truy vấn biết chunk đó thuộc phần nào của tài liệu. Nếu một section vượt quá `chunk_size`, hệ thống fallback sang `RecursiveChunker` để tách nhỏ dần theo cấp separator. Cách này giữ được semantic boundary tốt hơn so với cắt theo ký tự cố định.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Dữ liệu rapper có cấu trúc heading rõ ràng như tiểu sử, thành tích, trích dẫn, bảng thông tin. Chunk theo structure giúp mỗi chunk tập trung một chủ đề, nên query factoid match chính xác hơn. Khi kết hợp metadata filter theo `artist`, truy hồi giảm nhiễu mạnh ở các câu hỏi có tên nghệ sĩ cụ thể.

**Code snippet:**
```python
class DocumentStructureChunker:
	HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

	def __init__(self, chunk_size: int = 500) -> None:
		self.chunk_size = chunk_size
		self._fallback = RecursiveChunker(chunk_size=chunk_size)

	def chunk(self, text: str) -> list[str]:
		if not text:
			return []

		lines = text.splitlines()
		sections: list[tuple[str, str]] = []
		heading_stack: list[tuple[int, str]] = []
		buffer: list[str] = []

		def flush_current() -> None:
			body = "\n".join(buffer).strip()
			if not body:
				return
			path = " > ".join(title for _, title in heading_stack) if heading_stack else "Document"
			sections.append((path, body))

		for line in lines:
			match = self.HEADING_RE.match(line)
			if not match:
				buffer.append(line)
				continue

			flush_current()
			buffer = []

			level = len(match.group(1))
			title = match.group(2).strip()
			while heading_stack and heading_stack[-1][0] >= level:
				heading_stack.pop()
			heading_stack.append((level, title))

		flush_current()

		if not sections:
			return self._fallback.chunk(text)

		chunks: list[str] = []
		for path, body in sections:
			prefix = f"Section: {path}\n\n"
			if len(prefix) + len(body) <= self.chunk_size:
				chunks.append(prefix + body)
				continue

			for sub in self._fallback.chunk(body):
				candidate = (prefix + sub).strip()
				if len(candidate) <= self.chunk_size:
					chunks.append(candidate)
				else:
					chunks.extend(self._fallback.chunk(candidate))

		return [c for c in chunks if c.strip()]
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| full benchmark (5 queries) | best baseline: recursive_with_filter | 100 | - | Avg score = 0.4374 |
| full benchmark (5 queries) | **của tôi**: markdown_structure_with_filter | 110 | - | **Avg score = 0.4403 (cao nhất)** |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | DocumentStructureChunker + metadata filter | 8 | Giữ context theo section, lọc đúng nghệ sĩ | Số chunk tăng, chi phí indexing cao hơn |
| Nguyễn Tiến Thắng | RecursiveChunker + metadata filter | 9 | Cân bằng độ dài chunk, ổn định | Thiếu heading context so với strategy của tôi |
| Trần Anh Tú | RecursiveChunker + metadata filter | 8.5 | Cân bằng độ dài chunk, ổn định | Thiếu heading context so với strategy của tôi |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Với dữ liệu markdown theo tiểu mục, DocumentStructureChunker + metadata filter cho kết quả tốt nhất. Strategy này vừa giữ mạch nội dung theo section, vừa giới hạn không gian tìm kiếm theo `artist`. Tuy nhiên, kết quả của 2 bạn sử dụng RecursiveChunker + metadata filter đang cao hơn do sử dụng phương pháp Embedding khác nhau (Bài của em dùng LocalEmbedder còn của các bạn dùng OpenAIEmbedder) và chunk_size khác nhau, từ đó dẫn đến kết quả này.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**FixedSizeChunker.chunk** — approach:
> Phương pháp này cắt theo cửa sổ trượt với công thức bước nhảy step = chunk_size - overlap. Mỗi chunk có độ dài tối đa bằng chunk_size, chunk sau chồng lấn overlap ký tự so với chunk trước để giảm mất ngữ cảnh ở biên. Cách này đơn giản, tốc độ cao, dễ dự đoán số chunk, nhưng có thể cắt ngang câu và làm giảm tính mạch lạc ngữ nghĩa.

**SentenceChunker.chunk** — approach:
> Hàm chuẩn hóa input bằng strip, sau đó tách câu bằng regex (?<=[.!?])\s+ để giữ dấu câu ở cuối mỗi câu. Các câu được gom theo max_sentences_per_chunk để tạo chunk dễ đọc và giữ ngữ nghĩa tự nhiên. Edge case được xử lý gồm text rỗng, text chỉ chứa khoảng trắng, và trường hợp không tách được câu thì trả về nguyên văn bản.

**RecursiveChunker.chunk / _split** — approach:
> Thuật toán tách đệ quy theo thứ tự separator ưu tiên: xuống dòng kép, xuống dòng đơn, dấu chấm kèm khoảng trắng, khoảng trắng, và cuối cùng fallback cắt cứng theo ký tự. Base case là khi đoạn hiện tại nhỏ hơn hoặc bằng chunk_size, hoặc không còn separator để tách. Ở mỗi tầng đệ quy, hàm dùng buffer để ghép các mảnh nhỏ liền kề, nhằm tránh tạo quá nhiều chunk ngắn và vẫn đảm bảo không vượt ngưỡng kích thước.

**DocumentStructureChunker.chunk** — approach:
> Đây là chiến lược custom theo cấu trúc markdown: phát hiện heading bằng regex, lưu ngăn xếp tiêu đề để tạo breadcrumb theo từng section, rồi gắn prefix Section cho mỗi chunk. Khi section ngắn, giữ nguyên để tối đa hóa context; khi section dài, fallback sang RecursiveChunker để chia nhỏ nhưng vẫn bảo toàn thông tin tiêu đề. Cách này đặc biệt phù hợp với tài liệu có heading rõ ràng vì cải thiện khả năng truy hồi theo chủ đề và dễ truy vết nguồn thông tin.

**Tóm tắt khi dùng từng phương pháp:**
> FixedSize phù hợp baseline nhanh \
> Sentence phù hợp văn bản mô tả ngắn \
> Recursive là mặc định an toàn cho dữ liệu hỗn hợp \
> DocumentStructure phù hợp nhất với markdown nhiều mục và là lựa chọn chính của em trong benchmark

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Store hỗ trợ 2 backend: ChromaDB (nếu import được) hoặc in-memory list. Khi add, mỗi document được embed và lưu kèm metadata chuẩn hóa (auto set `doc_id` nếu thiếu). Khi search, query được embed rồi chấm điểm với từng chunk bằng dot product trên embedding vector, sau đó sort giảm dần theo `score` và cắt `top_k`.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` lọc metadata trước rồi mới tính similarity để tăng precision và giảm candidate nhiễu. Ở ChromaDB, filter đẩy xuống `where` trong query; ở in-memory, dùng điều kiện `all(metadata.get(k) == v ...)` trước khi scoring. `delete_document` xóa toàn bộ chunk theo `doc_id`: với Chroma truy vấn id rồi delete, với in-memory thì lọc lại danh sách và trả về boolean theo số phần tử bị giảm.

### KnowledgeBaseAgent

**`answer`** — approach:
> Hàm chuẩn hóa câu hỏi, retrieve `top_k` chunk từ store, rồi dựng prompt RAG theo dạng instruction + context + question. Mỗi context line có thứ tự và score để tăng tính minh bạch nguồn thông tin. Nếu không retrieve được gì hoặc LLM lỗi/trả rỗng, hàm fallback câu trả lời an toàn: "I don't have enough information to answer that.".

### Test Results

```
================================= test session starts =================================
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

================================= 42 passed in 0.15s =================================
```

**Số tests pass: 42 / 42**

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Python là một ngôn ngữ lập trình. | Python được dùng để xây dựng ứng dụng AI. | thấp | 0.0976 | Đúng |
| 2 | Rap Việt mùa 1 có Dế Choắt vô địch. | Dế Choắt là quán quân Rap Việt mùa đầu tiên. | cao | 0.4811 | Đúng |
| 3 | Suboi rap trước Barack Obama. | Tôi thích nấu phở bò vào cuối tuần. | thấp | 0.0003 | Đúng |
| 4 | ICD là quán quân King of Rap. | Karik là huấn luyện viên Rap Việt. | thấp | 0.1260 | Đúng |
| 5 | Wowy sáng lập SpaceSpeakers. | Wowy là người sáng lập nhóm rap SpaceSpeakers. | cao | 0.7071 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Cặp 1 khá bất ngờ vì dù cùng nhắc tới Python nhưng điểm vẫn thấp do biểu diễn token khác nhau nhiều. Điều này cho thấy nếu embedding hoặc vector hóa không đủ giàu ngữ nghĩa thì chỉ trùng một vài từ khóa chưa đủ để tạo độ tương đồng cao. Cặp 5 cho thấy khi chia sẻ nhiều token và chủ điểm cốt lõi thì cosine tăng rõ rệt.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer (tóm tắt) |
|---|-------|----------------------|
| 1 | Giới thiệu về một rapper đã từng là kẻ thù của ICD | MC ILL — rapper kiêm giáo viên tiếng Anh, từng diss ICD |
| 2 | Giới thiệu về Quán quân mùa 1 của chương trình Rap Việt | Dế Choắt — quán quân Rap Việt mùa 1, đội Wowy |
| 3 | Rapper Việt Nam từng rap cho cựu Tổng thống Barack Obama | Suboi — nữ hoàng hip-hop Việt Nam |
| 4 | Những ai là người từng ẩu đả với rapper Blacka? | Young H và B Ray — năm 2016, Blacka đánh gãy mũi B Ray |
| 5 | Giới thiệu về một rapper từng học Đại Học Kiến Trúc Hà Nội | Rhymastic — tốt nghiệp ĐH Kiến Trúc HN, nhóm SpaceSpeakers |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Giới thiệu về một rapper đã từng là kẻ thù của ICD | Top-1 từ icd: ICD từng diss khá nhiều rapper (nêu bối cảnh beef, chưa liệt kê đủ danh sách). | 0.7839 | Có | Trả lời theo hướng ICD có nhiều đối thủ, nhưng thiếu đầy đủ các tên như gold answer. |
| 2 | Giới thiệu về Quán quân mùa 1 của chương trình Rap Việt | Top-1 từ suboi chỉ chứa cụm liên quan Rap Việt; thông tin về Dế Choắt nằm ở top-2. | 0.6940 | Một phần | Câu trả lời chưa chính xác ở top-1, cần thêm ngữ cảnh từ chunk de_choat để đầy đủ. |
| 3 | Rapper Việt Nam từng rap cho cựu Tổng thống Barack Obama | Top-1 từ suboi nêu trực tiếp việc rap trước Barack Obama. | 0.8108 | Có | Suboi là rapper từng rap cho cựu Tổng thống Barack Obama khi thăm Việt Nam. |
| 4 | Những ai là người từng ẩu đả với rapper Blacka? | Top-1 bị lệch sang icd; thông tin Blacka chỉ xuất hiện ở kết quả thấp hơn. | 0.6552 | Không | Câu trả lời chưa đúng, thiếu thông tin Young H và B Ray theo đáp án chuẩn. |
| 5 | Giới thiệu về một rapper từng học Đại Học Kiến Trúc Hà Nội | Top-1 bị lệch sang icd, không truy hồi đúng Rhymastic. | 0.6602 | Không | Câu trả lời chưa đúng với gold answer về Rhymastic. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 3 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Bài học rõ nhất từ các bạn trong nhóm là phải kết hợp metadata filter ngay từ bước retrieval, đặc biệt với bộ dữ liệu có nhiều thực thể (tên rapper) dễ gây nhiễu. Kết quả của em cho thấy khi không ràng buộc đủ mạnh theo metadata, hệ thống dễ trả về chunk lệch chủ đề (ví dụ query về Blacka hoặc Rhymastic nhưng top-1 lại rơi vào ICD). So với chỉ tinh chỉnh chunk size, việc thiết kế filter hợp lý tạo cải thiện rõ rệt hơn về độ chính xác. Ngoài ra, cần chọn phương pháp trích xuất embedding hợp lý để trả về kết quả tối ưu nhất.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Qua demo, điều em học được rõ nhất là cách các nhóm khác biểu diễn bộ tiêu chí đánh giá một cách đa dạng và rõ ràng. Họ không chỉ nhìn một chỉ số duy nhất mà tách riêng các góc như độ liên quan của chunk, tính đúng của câu trả lời, mức grounding theo ngữ cảnh và phân tích lỗi theo từng truy vấn. Cách trình bày này giúp so sánh công bằng hơn giữa các chiến lược và làm phần kết luận thuyết phục hơn.

**Failure case trong quá trình so sánh:**
> **Query thất bại:** "Những ai là người từng ẩu đả với rapper Blacka?" (query 4).
>
> **Biểu hiện thất bại:** Top-1 retrieval bị lệch sang chunk của ICD, trong khi thông tin đúng về Blacka chỉ xuất hiện ở kết quả thấp hơn. Vì vậy agent trả lời thiếu người liên quan (Young H, B Ray) và grounding yếu.
>
> **Phân tích nguyên nhân theo tiêu chí:**
> - **Precision:** Top-1 không đúng thực thể mục tiêu, nên precision ở mức cao nhất bị giảm mạnh.
> - **Chunk coherence:** Chunk của Blacka chưa đủ nổi bật tín hiệu "ẩu đả" so với các chunk khác có từ vựng gần nghĩa về conflict/beef.
> - **Metadata utility:** Chưa tận dụng filter theo thực thể (`artist = blacka`) cho truy vấn có tên riêng rõ ràng.
> - **Grounding quality:** Câu trả lời cuối không bám chặt vào chứng cứ truy hồi top đầu, dẫn đến thiếu fact quan trọng.
>
> **Đề xuất cải thiện:**
> 1. Áp dụng metadata filter theo tên nghệ sĩ khi query chứa thực thể rõ (ví dụ Blacka, Rhymastic).
> 2. Tăng trọng số lexical/entity matching ở bước rerank để ưu tiên chunk có thực thể trùng exact-match.
> 3. Tái chunk các đoạn tiểu sử dài thành chunk theo sự kiện (beef, giải thưởng, học vấn) để tăng coherence.
> 4. Thêm bước kiểm tra grounding: chỉ xuất câu trả lời khi có ít nhất 1 chunk top-k chứa đủ entity và fact chính.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, em sẽ chuẩn hóa dữ liệu kỹ hơn trước khi index (sửa lỗi chính tả, tách đoạn chứa fact quan trọng, bổ sung mốc thời gian/sự kiện). Em cũng sẽ mở rộng metadata ngoài `artist` như `topic` và `entity` để lọc sát ý định truy vấn, từ đó giảm lỗi truy hồi lệch như ở query 4 và 5. Cuối cùng, em sẽ benchmark theo nhiều cấu hình embedder/chunk_size trên cùng bộ câu hỏi để so sánh công bằng hơn giữa các thành viên.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 9 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **86 / 90** |
