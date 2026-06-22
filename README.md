# Universal Algorithmic Oracle (UAO) v0.2.0

**یک سیستم تکاملی تطبیقی برای تولید خروجی‌های نمادین از سوالات دلخواه**

---

## فهرست مطالب

1. [معرفی کلی](#۱-معرفی-کلی)
2. [هدف پروژه](#۲-هدف-پروژه)
3. [معماری سیستم](#۳-معماری-سیستم)
4. [ساختار دایرکتوری](#۴-ساختار-دایرکتوری)
5. [راهنمای نصب و راه‌اندازی](#۵-راهنمای-نصب-و-راهاندازی)
6. [نحوه استفاده](#۶-نحوه-استفاده)
7. [توضیح ماژول‌ها](#۷-توضیح-ماژولها)
8. [سیستم‌های نمادین](#۸-سیستمهای-نمادین)
9. [موتورهای تکاملی](#۹-موتورهای-تکاملی)
10. [سیستم ارزیابی](#۱۰-سیستم-ارزیابی)
11. [حافظه و ماندگاری](#۱۱-حافظه-و-ماندگاری)
12. [پیکربندی](#۱۲-پیکربندی)
13. [تست‌ها](#۱۳-تستها)
14. [نمودار جریان داده](#۱۴-نمودار-جریان-داده)
15. [مشکلات شناخته‌شده](#۱۵-مشکلات-شناخته‌شده)
16. [ نقشه راه آینده](#۱۶-نقشه-راه-آینده)

---

## ۱. معرفی کلی

**Universal Algorithmic Oracle** یک سیستم نرم‌افزاری پیچیده است که بیش از ۴۰ سیستم نمادین و طالع‌بینی از فرهنگ‌های مختلف جهان را در یک موتور تکاملی یکپارچه می‌کند. این سیستم با استفاده از الگوریتم‌های ژنتیک، برنامه‌سازی ژنتیکی و بهینه‌سازی چندهدفه، ساختارهای نمادین را برای پاسخگویی به سوالات تکامل می‌دهد.

### ویژگی‌های کلیدی

- **بیش از ۴۰ سیستم نمادین** از سنت‌های مختلف (غربی، شرقی، عربی، چینی، مایا، و ...)
- **۲۴ موتور تکاملی** شامل GA، GP، NSGA-II و بهینه‌سازهای خارجی
- **مدل جزیره‌ای** برای تکامل موازی خانواده‌های مختلف سیستم‌ها
- **سیستم ارزیابی چندهدفه** با ۹ بُعد fitness
- **حافظه تکاملی** با ردیابی خط سیر، بانک جهش و آرشیو کروموزوم
- **خروجی چندفرمتی** (JSON, HTML, PDF, Markdown, Text)
- **رابط کاربری فارسی/عربی** با پشتیبانی از متن فارسی

---

## ۲. هدف پروژه

این سیستم با هدف ایجاد یک **موتور جستجوی نمادین خودتکاملی** طراحی شده که:

1. **ترکیب سیستم‌های نمادین**: اتصال بیش از ۴۰ سیستم طالع‌بینی و نمادشناسی در یک چارچوب یکپارچه
2. **تکامل خودکار**: بهبود مداوم ساختارهای نمادین از طریق الگوریتم‌های تکاملی
3. **تطبیق پذیری**: یادگیری از نتایج گذشته و تطبیق با سوالات جدید
4. **مشاهده‌پذیری کامل**: ردیابی کامل خط سیر تکامل و تاریخچه تصمیمات
5. **قابلیت اطمینان**: آزمایش‌های کور تاریخی و ارزیابی عملکرد پیش‌بینی

---

## ۳. معماری سیستم

### نمودار لایه‌ای

```
┌─────────────────────────────────────────────────────┐
│                  لایه رابط کاربری                      │
│         main.py (CLI) + Interface Layer              │
├─────────────────────────────────────────────────────┤
│               لایه لوله‌کشی (Pipeline)                 │
│    OraclePipeline → Entropy → Evolution → Fusion     │
├─────────────────────────────────────────────────────┤
│                 لایه تکامل                             │
│  GA/GP/NSGA-II + 24 Engine + Island Model           │
├─────────────────────────────────────────────────────┤
│                لایه نمادین                             │
│        40+ Symbolic Systems + Wrappers               │
├─────────────────────────────────────────────────────┤
│               لایه ژنوم                               │
│    Gene → Chromosome → Oracle Structure              │
├─────────────────────────────────────────────────────┤
│              لایه ارزیابی                             │
│   Fitness (9D) + Benchmark + External Trials         │
├─────────────────────────────────────────────────────┤
│               لایه حافظه                              │
│    Archive + Lineage + Mutation Bank + Registry      │
├─────────────────────────────────────────────────────┤
│              لایه آنتروپی                             │
│     Entropy Encoding + Bitstream + Hashing           │
└─────────────────────────────────────────────────────┘
```

### جریان داده

```
سوال کاربر
    │
    ▼
┌──────────────────┐
│  Entropy Encoder  │ ──→ EntropyPacket
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  Population Init  │ ──→ Random Chromosomes
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  Evolution Loop   │ ◄── Fitness Evaluation
│  (GA/GP/NSGA-II)  │ ◄── Mutation Operators
│                   │ ◄── Crossover Operators
│                   │ ◄── Selection
│                   │ ◄── Island Migration
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  Best Chromosome  │ ──→ Execute on EntropyPacket
└──────────────────┘
    │
    ▼
┌──────────────────┐
│   Fusion Layer    │ ──→ Combined Output
└──────────────────┘
    │
    ▼
┌──────────────────┐
│  Oracle Output    │ ──→ Answer + Confidence + Explanation
└──────────────────┘
```

---

## ۴. ساختار دایرکتوری

```
universal_algorithmic_oracle/
│
├── config/                          # فایل‌های پیکربندی YAML
│   ├── settings.yaml                # تنظیمات کلی پروژه
│   ├── evolution.yaml               # پارامترهای تکامل
│   ├── fitness.yaml                 # وزن‌های ارزیابی fitness
│   ├── systems.yaml                 # لیست سیستم‌های نمادین
│   └── oracle.yaml                  # تنظیمات oracle
│
├── data/                            # داده‌های تست و نمونه
│
├── experiments/                     # لاگ آزمایش‌ها
│
├── oracle/                          # بسته اصلی نرم‌افزار
│   ├── __init__.py                  # خروجی‌های عمومی
│   │
│   ├── entropy/                     # رمزگذاری آنتروپی ورودی
│   │   ├── encoder.py               # EntropyEncoder اصلی
│   │   ├── bitstream.py             # عملیات بیت‌استریم
│   │   ├── hashing.py               # هش‌سازی SHA-256
│   │   ├── calendar_entropy.py      # آنتروپی تقویمی
│   │   └── symbolic_matrix.py       # ماتریس نمادین
│   │
│   ├── symbolic/                    # ۴۰+ سیستم نمادین
│   │   ├── base.py                  # SymbolicSystemWrapper (ABC)
│   │   ├── registry.py              # رجیستری سیستم‌ها
│   │   ├── modifiable.py            # سیستم‌های قابل تغییر
│   │   ├── astrology/               # طالع‌بینی غربی، ودیک
│   │   ├── binary/                  # IChing، جومانسی، رمل
│   │   ├── cards/                   # تاروت، رون‌ها، لینورماند
│   │   ├── dreams/                  # نمادهای رویا
│   │   ├── eastern/                 # بازی، زیویی، قیمن، باری
│   │   ├── fortune_telling/         # عددشناسی، اعداد مثلثی
│   │   ├── gematria/                # گماتریا عبری، انگلیسی، عبجد
│   │   ├── mayan/                   # تقویم مایا
│   │   └── numerical/               # سیستم‌های عددی
│   │
│   ├── genome/                      # نمایش ژنوم
│   │   ├── gene.py                  # Gene (واحد پایه)
│   │   ├── chromosome.py            # Chromosome (ساختار نمادین)
│   │   ├── oracle_structure.py      # OracleStructure
│   │   ├── tree_genome.py           # نمایش درختی (GP)
│   │   ├── graph_genome.py          # نمایش گرافی
│   │   ├── hybrid_genome.py         # نمایش ترکیبی
│   │   └── serialization.py         # سریال‌سازی
│   │
│   ├── evolution/                   # الگوریتم‌های تکاملی
│   │   ├── deap_engine.py           # موتور GA اصلی
│   │   ├── gp_engine.py             # موتور GP
│   │   ├── nsga_engine.py           # موتور NSGA-II
│   │   ├── selection.py             # عملگرهای انتخاب
│   │   ├── crossover.py             # عملگرهای تقاطع
│   │   ├── mutation.py              # عملگرهای جهش
│   │   ├── deep_mutation.py         # جهش عمیق
│   │   ├── expansion.py             # گسترش ساختاری
│   │   ├── pruning.py               # هرس کردن
│   │   ├── rule_invention.py        # ابداع قوانین جدید
│   │   ├── novelty.py               # امتیاز نوآوری
│   │   ├── population.py            # مدیریت جمعیت
│   │   ├── diversity_controller.py  # کنترل تنوع
│   │   ├── progressive_difficulty.py # سختی پیشرفته
│   │   ├── engines/                 # ۱۶ موتور خارجی
│   │   │   ├── pygad_engine.py
│   │   │   ├── mealpy_engine.py
│   │   │   ├── nevergrad_engine.py
│   │   │   ├── evosax_engine.py
│   │   │   └── ... (۱۶ موتور)
│   │   └── islands/                 # مدل جزیره‌ای
│   │       ├── island_model.py      # Island + IslandModel
│   │       ├── migration.py         # مدیریت مهاجرت
│   │       └── scheduler.py         # زمان‌بندی جزیره‌ها
│   │
│   ├── evaluation/                  # ارزیابی و معیارها
│   │   ├── fitness.py               # FitnessEvaluator (9D)
│   │   ├── coherence.py             # هماهنگی ساختاری
│   │   ├── stability.py             # پایداری عددی
│   │   ├── convergence.py           # تشخیص همگرایی
│   │   ├── complexity.py            # امتیاز پیچیدگی
│   │   ├── benchmark.py             # معیار پیش‌بینی
│   │   └── external_trials.py       # آزمایش‌های خارجی
│   │
│   ├── fusion/                      # ترکیب خروجی سیستم‌ها
│   │   ├── mapping.py               # نگاشت خروجی
│   │   ├── symbolic_fusion.py       # ترکیب نمادین
│   │   ├── numeric_fusion.py        # ترکیب عددی
│   │   ├── graph_fusion.py          # ترکیب گرافی
│   │   └── evolved_fusion.py        # ترکیب تکاملی
│   │
│   ├── memory/                      # حافظه و ماندگاری
│   │   ├── archive.py               # حافظه تکاملی (SQLite)
│   │   ├── chromosome_archive.py    # آرشیو کروموزوم
│   │   ├── lineage.py               # ردیابی خط سیر
│   │   ├── mutation_bank.py         # بانک جهش‌ها
│   │   ├── fitness_history.py       # تاریخچه fitness
│   │   ├── experiment_ledger.py     # دفتر آزمایش‌ها
│   │   ├── oracle_registry.py       # رجیستری oracle
│   │   ├── generational_memory.py   # حافظه نسلی
│   │   ├── graph_store.py           # ذخیره گرافی
│   │   └── symbolic_archive.py      # آرشیو خروجی نمادین
│   │
│   ├── interface/                   # رابط کاربری
│   │   ├── question.py              # تحلیلگر سوال
│   │   ├── normalization.py         # نرمال‌سازی متن
│   │   └── schemas.py               # اسکیمای ورودی/خروجی
│   │
│   ├── output/                      # تولید خروجی
│   │   ├── oracle_output.py         # OracleOutput
│   │   ├── explanation.py           # سازنده توضیحات
│   │   ├── report.py                # تولید گزارش
│   │   └── visualization.py         # تجسم‌سازی
│   │
│   └── runtime/                     # اجرای سیستم
│       ├── executor.py              # OraclePipeline (هماهنگ‌کننده اصلی)
│       ├── pipeline.py              # لوله‌کشی پایین‌سطح
│       ├── cache.py                 # کش نتایج
│       └── sandbox.py               # اجرای ایمن
│
├── tests/                           # تست‌ها
│   ├── test_all.py                  # تست یکپارچه کامل
│   ├── test_entropy.py              # تست آنتروپی
│   ├── test_genome.py               # تست ژنوم
│   ├── test_wrappers.py             # تست سیستم‌های نمادین
│   ├── test_fitness.py              # تست ارزیابی
│   ├── test_memory.py               # تست حافظه
│   ├── test_mutation.py             # تست جهش
│   └── test_crossover.py            # تست تقاطع
│
├── main.py                          # نقطه ورود CLI
├── pyproject.toml                   # اطلاعات پروژه و وابستگی‌ها
├── طرح نهایی الگریتم پیشگو.txt       # سند طراحی اصلی
└── README.md                        # این فایل
```

---

## ۵. راهنمای نصب و راه‌اندازی

### پیش‌نیازها

- Python ≥ 3.11
- pip

### نصب وابستگی‌های پایه

```bash
pip install click numpy pyyaml jinja2
```

### نصب وابستگی‌های اختیاری (برای موتورهای خارجی)

```bash
# موتورهای ژنتیک
pip install pygad geneticalgorithm2 pyeasyga

# برنامه‌سازی ژنتیکی
pip install gplearn karoo_gp

# بهینه‌سازی پیشرفته
pip install nevergrad mealpy niapy evosax

# چندهدفه
pip install pymoo pygmo

# عصب‌تکامل
pip install neat-python

# AutoML
pip install tpot

# فوتوکاپی
pip install pyswarm pymetaheuristic
```

### نصب پروژه

```bash
cd universal_algorithmic_oracle
pip install -e .
```

### تست نصب

```bash
python tests/test_all.py
```

---

## ۶. نحوه استفاده

### استفاده از خط فرمان (CLI)

```bash
# سوال ساده
python main.py ask "آیا این پروژه موفق می‌شود؟"

# با تعداد نسل‌های مشخص
python main.py ask "بهترین مسیر زندگی من چیست؟" --generations 300

# با موتور خاص
python main.py ask "سوال من" --engine pymoo

# لیست سیستم‌های نمادین
python main.py list-systems

# بنچمارک
python main.py benchmark

# خروجی JSON
python main.py export results.json --format json
```

### استفاده از کد پایتون

```python
from oracle.runtime.executor import OraclePipeline

# ایجاد نمونه
pipeline = OraclePipeline()

# ارسال سوال
output = pipeline.ask("آیا این پروژه موفق می‌شود؟", generations=200)

# نمایش نتیجه
print(f"پاسخ: {output.answer}")
print(f"اطمینان: {output.confidence}")
print(f"توضیح: {output.explanation}")

# خروجی کامل
print(output.to_dict())
```

### استفاده از موتور GP (برنامه‌سازی ژنتیکی)

```python
output = pipeline.ask_tree("سوال من", generations=100)
```

### استفاده از NSGA-II (بهینه‌سازی چندهدفه)

```python
output = pipeline.ask("سوال من", generations=200, engine='nsga')
```

---

## ۷. توضیح ماژول‌ها

### ۷.۱ ماژول آنتروپی (`oracle/entropy/`)

این ماژول ورودی خام (متن سوال) را به بسته‌های آنتروپی تبدیل می‌کند.

#### `entropy/encoder.py`

```python
class EntropyEncoder:
    """رمزگذار اصلی آنتروپی"""
    
    def encode(self, question: str, timestamp=None) -> EntropyPacket:
        """
        تبدیل سوال به بسته آنتروپی
        
        مراحل:
        1. نرمال‌سازی متن
        2. تولید SHA-256 hash
        3. تبدیل hash به بیت‌استریم
        4. استخراج بردار عددی از کاراکترها
        5. تولید زمینه تقویمی
        6. تولید ماتریس نمادین
        """
```

**خروجی `EntropyPacket`:**

```python
@dataclass
class EntropyPacket:
    raw_question: str              # سوال اصلی
    normalized_text: str           # متن نرمال‌شده
    seed: int                      # بذر عددی
    bit_stream: list[int]          # بیت‌استریم (256 بیت)
    numeric_vector: list[float]    # بردار عددی
    sha_stream: str                # رشته SHA-256
    calendar_context: dict         # زمینه تقویمی
    symbolic_matrix: list          # ماتریس نمادین
    timestamp: datetime            # زمان
```

#### `entropy/bitstream.py`

عملیات سطح پایین روی بیت‌استریم:

```python
class BitStream:
    def from_hex(hex_str: str) -> BitStream    # از هگز
    def to_hex() -> str                        # به هگز
    def xor(other: BitStream) -> BitStream     # XOR
    def rotate(n: int) -> BitStream            # چرخش
    def hamming_distance(other) -> int         # فاصله همینگ
    def population_count() -> int              # تعداد بیت‌های 1
```

#### `entropy/hashing.py`

```python
def hash_text(text, algorithm='sha256') -> str     # هش متن
def hash_to_bits(hash_str) -> list[int]            # تبدیل به بیت
def derive_seed(text, salt='') -> int              # استخراج بذر
```

#### `entropy/calendar_entropy.py`

```python
def generate_calendar_entropy(timestamp=None) -> dict:
    """
    تولید آنتروپی از تقویم
    خروجی:gregorian, jalali, hijri, numeric_signature
    """
```

#### `entropy/symbolic_matrix.py`

```python
def generate_symbolic_matrix(seed, shape=(8,8)) -> list[list[float]]
def matrix_to_features(matrix) -> dict  # mean, variance, entropy
```

---

### ۷.۲ ماژول ژنوم (`oracle/genome/`)

ساختارهای داده‌ای برای نمایش راه‌حل‌های نمادین.

#### `genome/gene.py` - واحد پایه

```python
@dataclass
class Gene:
    """ژن - واحد پایه ساختار نمادین"""
    gene_id: str                    # شناسه یکتا
    system_id: str                  # شناسه سیستم نمادین (مثلاً "gematria")
    backend: str                    # بک‌اند ("internal" یا نام خارجی)
    gene_type: str                  # نوع ژن
    params: dict                    # پارامترهای سیستم
    input_slots: list[str]          # ورودی‌ها
    output_slots: list[str]         # خروجی‌ها
    weight: float                   # وزن (0.0 تا 1.0)
    mutation_policy: dict           # سیاست جهش
    
    def mutate(self, rate) -> Gene  # جهش پارامتری
```

#### `genome/chromosome.py` - ساختار نمادین

```python
@dataclass
class Chromosome:
    """کروموزوم - ساختار نمادین کامل"""
    chromosome_id: str              # شناسه یکتا
    genes: dict[str, Gene]          # ژن‌ها (دیکشنری)
    edges: list[tuple[str,str]]     # یال‌های گراف
    fusion_schema: dict             # الگوی ترکیب
    fusion_rules: list[dict]        # قوانین ترکیب
    output_mapping: dict            # نگاشت خروجی
    fitness: dict                   # امتیاز fitness
    system_configs: dict            # پیکربندی سیستم‌ها
    custom_formulas: dict           # فرمول‌های سفارشی
    invented_methods: list          # روش‌های ابداعی
    metadata: dict                  # فراداده
    memory_links: list[str]         # پیوندهای حافظه
    generation: int                 # نسل
    
    @property
    def gene_list(self) -> list[Gene]
    
    def execute(self, entropy_packet) -> dict:
        """
        اجرای ساختار روی بسته آنتروپی
        
        مراحل:
        1. مرتب‌سازی توپولوژیکی ژن‌ها
        2. اجرای هر ژن روی سیستم نمادین مربوطه
        3. ترکیب خروجی‌ها با fusion_schema
        """
    
    def crossover(self, other) -> Chromosome     # تقاطع
    def mutate(self, rate) -> Chromosome         # جهش
    
    @classmethod
    def create_random(cls, systems=None) -> Chromosome
```

#### `genome/tree_genome.py` - نمایش درختی (GP)

```python
class TreeNode:
    """گره درخت"""
    node_id: str
    value: str
    children: list[TreeNode]
    node_type: str  # "operator" یا "terminal"
    
    def evaluate(self, inputs) -> float

class TreeGenome:
    """ژنوم درختی برای برنامه‌سازی ژنتیکی"""
    root: TreeNode
    max_depth: int
    operators: list[str]    # ["+", "-", "*", "/", "sin", "cos", ...]
    terminals: list[str]    # ["x", "y", "n", "t", "h", "s", "e", ...]
    
    def random_tree(self, depth) -> TreeNode
    def to_chromosome(self) -> Chromosome
```

#### `genome/graph_genome.py` - نمایش گرافی

```python
class GraphGenome:
    """ژنوم گرافی"""
    genome_id: str
    nodes: dict
    edges: list[tuple]
    
    @classmethod
    def random(cls, genome_id, size, ...) -> GraphGenome
    
    def to_chromosome(self) -> Chromosome
```

#### `genome/hybrid_genome.py` - نمایش ترکیبی

```python
class HybridGenome:
    """ترکیب درخت + گراف + خطی"""
    tree: TreeGenome
    graph: GraphGenome
    linear: Chromosome
    
    def to_chromosome(self) -> Chromosome
    
    @classmethod
    def from_chromosome(cls, chrom) -> HybridGenome
```

#### `genome/serialization.py`

```python
def serialize_chromosome(chrom) -> bytes       # سریال‌سازی
def deserialize_chromosome(data) -> Chromosome # بازیابی
def serialize_population(pop) -> bytes         # سریال‌سازی جمعیت
def deserialize_population(data) -> list[Chromosome]
```

---

### ۷.۳ ماژول تکامل (`oracle/evolution/`)

الگوریتم‌های تکاملی برای بهبود ساختارهای نمادین.

#### `evolution/deap_engine.py` - موتور GA اصلی

```python
class EvolutionaryEngine:
    """موتور ژنتیک اصلی"""
    
    def __init__(self, config: dict):
        self.population_size = config.get("population_size", 50)
        self.elite_count = config.get("elite_count", 5)
        self.generations = config.get("max_generations", 200)
    
    def initialize_population(self, systems):
        """ایجاد جمعیت اولیه تصادفی"""
    
    def evolve(self, entropy_packet, generations=200) -> list[Chromosome]:
        """
        حلقه تکامل
        
        هر نسل:
        1. ارزیابی fitness تمام کروموزوم‌ها
        2. انتخاب والدین (tournament + elitism)
        3. اعمال تقاطع
        4. اعمال جهش
        5. گسترش/هرس ساختار
        6. ابداع قوانین جدید
        7. کنترل تنوع
        8. ضبط در حافظه تکاملی
        """
    
    def get_best(self) -> Chromosome
    def get_elite(self, count) -> list[Chromosome]
```

#### `evolution/mutation.py` - عملگرهای جهش

```python
# ۷ نوع جهش

def param_mutation(chromosome, rate) -> Chromosome:
    """جهش پارامتری - نویز گاوسی روی وزن‌ها"""

def structural_mutation(chromosome, rate) -> Chromosome:
    """جهش ساختاری - جابجایی system_id، اضافه کردن یال"""

def civilization_mutation(chromosome, rate) -> Chromosome:
    """جهش تمدنی - جابجایی ژن بین خانواده‌ها"""

def dimensional_mutation(chromosome, rate) -> Chromosome:
    """جهش بُعدی - اضافه کردن dimension_shift"""

def rule_making_mutation(chromosome, rate) -> Chromosome:
    """جهش قانون‌سازی - تغییر fusion_schema"""

def anti_traditional_mutation(chromosome, rate) -> Chromosome:
    """جهش ضدارثباتی - اضافه کردن anti_traditional"""

def deep_system_mutation(chromosome, rate, difficulty) -> Chromosome:
    """جهش عمیق - تغییر منطق داخلی سیستم"""

ALL_MUTATIONS = [param_mutation, structural_mutation, civilization_mutation,
                 dimensional_mutation, rule_making_mutation, 
                 anti_traditional_mutation, deep_system_mutation]
```

#### `evolution/crossover.py` - عملگرهای تقاطع

```python
# ۵ نوع تقاطع

def uniform_crossover(p1, p2, rate) -> tuple[Chromosome, Chromosome]:
    """تقاطع یکنواخت - جابجایی ژن‌ها با نرخ مشخص"""

def subgraph_crossover(p1, p2) -> tuple[Chromosome, Chromosome]:
    """تقاطع زیرگرافی - جابجایی زیرگراف‌ها"""

def civilization_crossover(p1, p2) -> tuple[Chromosome, Chromosome]:
    """تقاطع تمدنی - تبادل ژن‌های خانواده‌ای"""

def rule_based_crossover(p1, p2) -> tuple[Chromosome, Chromosome]:
    """تقاطع مبتنی بر قانون - ادغام قوانین ترکیب"""

def memory_based_crossover(p1, p2) -> tuple[Chromosome, Chromosome]:
    """تقاطع مبتنی بر حافظه - ادغام پیوندهای حافظه"""

ALL_CROSSOVERS = [uniform_crossover, subgraph_crossover,
                  civilization_crossover, rule_based_crossover,
                  memory_based_crossover]
```

#### `evolution/selection.py` - عملگرهای انتخاب

```python
def tournament_selection(pop, size) -> Chromosome
def roulette_selection(pop) -> Chromosome
def rank_selection(pop) -> Chromosome
def elitism_select(pop, count) -> list[Chromosome]
def nsga_tournament_selection(pop, size) -> Chromosome  # برای NSGA-II
```

#### `evolution/expansion.py` - گسترش ساختاری

```python
def expand_chromosome(chrom, rate) -> Chromosome:
    """اضافه کردن ژن جدید تصادفی"""

def contract_chromosome(chrom, rate) -> Chromosome:
    """حذف ژن تصادفی"""

def add_connection(chrom, rate) -> Chromosome:
    """اضافه کردن یال جدید"""
```

#### `evolution/pruning.py` - هرس کردن

```python
class PruningEngine:
    """موتور هرس - حذف ژن‌های ضعیف"""
    
    def __init__(self, prune_threshold=0.1, min_genes=1):
        self.prune_threshold = prune_threshold
        self.min_genes = min_genes
    
    def prune(self, chromosome) -> Chromosome:
        """حذف ژن‌هایی با وزن کمتر از آستانه"""
```

#### `evolution/rule_invention.py` - ابداع قوانین جدید

```python
class RuleInventionEngine:
    """موتور ابداع قوانین"""
    
    RULE_TEMPLATES = [...]
    CALCULATION_METHODS = [...]
    COMBINATION_STRATEGIES = [...]
    
    def invent_rules(self, chromosome) -> Chromosome:
        """
        ابداع انواع قوانین:
        - قوانین ترکیب
        - قوانین فرمولی
        - روش‌های جدید
        - استراتژی‌ها
        - ترکیبی
        """
```

#### `evolution/novelty.py` - امتیاز نوآوری

```python
def compute_novelty(chromosome, archive, k=15) -> float:
    """
    محاسبه نوآوری بر اساس فاصله k-نزدیک‌ترین همسایه
    هرچه فاصله بیشتر → نوآوری بالاتر
    """
```

#### `evolution/deep_mutation.py` - جهش عمیق

```python
class DeepMutationEngine:
    """موتور جهش عمیق - تغییر منطق داخلی سیستم‌ها"""
    
    def mutate_system(self, modifiable_system, intensity, entropy_packet):
        """
        انواع جهش عمیق:
        - _mutate_parameters: تغییر پارامترها
        - _invent_formula: ابداع فرمول جدید
        - _change_transforms: تغییر تبدیلات
        - _rebuild_structure: بازسازی ساختار
        - _hybrid_mutation: جهش ترکیبی
        - _mutate_scale: تغییر مقیاس
        """
```

#### `evolution/islands/` - مدل جزیره‌ای

```python
# خانواده‌های سیستم‌ها برای جزیره‌ها
ISLAND_FAMILIES = {
    "western": [("gematria", "internal"), ("calendar", "internal")],
    "eastern": [("iching", "internal"), ("calendar", "internal")],
    "binary": [("iching", "internal"), ("geomancy", "internal")],
    "letter_number": [("gematria", "internal"), ("numerology", "internal")],
    "hybrid": [("gematria", "internal"), ("iching", "internal"), 
               ("geomancy", "internal")],
}

class IslandModel:
    """مدل جزیره‌ای - تکامل موازی"""
    
    def __init__(self, config):
        self.num_islands = config.get("num_islands", 4)
        self.migration_interval = config.get("migration_interval", 10)
        self.migration_rate = config.get("migration_rate", 0.1)
    
    def evolve(self, entropy_packet, generations, callback=None):
        """
        تکامل در جزیره‌های مختلف با مهاجرت دوره‌ای
        
        1. هر جزیره به طور مستقل تکامل می‌یابد
        2. هر N نسل، بهترین‌ها بین جزیره‌ها مهاجرت می‌کنند
        3. در نهایت، بهترین کروموزوم از تمام جزیره‌ها انتخاب می‌شود
        """
```

#### `evolution/engines/` - ۱۶ موتور خارجی

| موتور | کتابخانه | نوع |
|-------|----------|-----|
| PyGADEngine | `pygad` | GA |
| GeneticAlgorithm2Engine | `geneticalgorithm2` | GA |
| PyEasyGAEngine | `pyeasyga` | GA |
| InspyredEngine | `inspyred` | EC |
| GPlearnEngine | `gplearn` | Symbolic Regression |
| TpotEngine | `tpot` | AutoML |
| KarooGPEngine | `karoo_gp` | GP |
| NevergradEngine | `nevergrad` | Optimization |
| EvosaxEngine | `evosax` | Evolution Strategies |
| PyGMOEngine | `pygmo` | Island Model |
| PyMOOEngine | `pymoo` | NSGA-II |
| PySwarmEngine | `pyswarms` | PSO |
| MealpyEngine | `mealpy` | PSO/GA |
| NiaPyEngine | `niapy` | DE/PSO |
| PyMetaheuristicEngine | `pymetaheuristic` | GA/PSO |
| NEATEngine | `neat` | Neuroevolution |

---

### ۷.۴ ماژول ارزیابی (`oracle/evaluation/`)

#### `evaluation/fitness.py` - ارزیاب چندهدفه

```python
class FitnessEvaluator:
    """ارزیاب fitness با ۹ بُعد"""
    
    # وزن‌های پیش‌فرض
    DEFAULT_WEIGHTS = {
        "structural_coherence": 0.15,    # هماهنگی ساختاری
        "symbolic_diversity": 0.12,      # تنوع نمادین
        "numerical_coherence": 0.10,     # هماهنگی عددی
        "information_density": 0.08,     # تراکم اطلاعات
        "temporal_alignment": 0.08,      # هم‌راستایی زمانی
        "complexity_penalty": 0.07,      # جریمه پیچیدگی
        "novelty_bonus": 0.05,           # پاداش نوآوری
        "prediction_accuracy": 0.20,     # دقت پیش‌بینی
    }
    
    def evaluate(self, chromosome, entropy_packet) -> dict:
        """
        ارزیابی چندهدفه
        
        خروجی:
        {
            "structural_coherence": float,
            "symbolic_diversity": float,
            "numerical_coherence": float,
            "information_density": float,
            "temporal_alignment": float,
            "complexity_penalty": float,
            "novelty_bonus": float,
            "prediction_accuracy": float,
            "total_fitness": float
        }
        """
```

#### `evaluation/coherence.py`

```python
def structural_coherence(chromosome) -> float:
    """
    محاسبه هماهنگی ساختاری
    - تراکم یال‌ها
    - تنوع سیستم‌ها
    """
```

#### `evaluation/stability.py`

```python
def numerical_stability(chromosome) -> float:
    """
    محاسبه پایداری عددی
    - واریانس وزن‌ها
    - ثبات ترکیب
    """
```

#### `evaluation/convergence.py`

```python
class ConvergenceDetector:
    """تشخیص همگرایی"""
    
    def __init__(self, threshold=0.001, patience=10):
        self.history = []
        self.threshold = threshold
        self.patience = patience
    
    def is_converged(self) -> bool:
        """آیا الگوریتم همگرا شده؟"""
    
    def get_convergence_rate(self) -> float:
        """نرخ همگرایی"""
```

#### `evaluation/complexity.py`

```python
def complexity_score(chromosome) -> float:
    """
    محاسبه پیچیدگی
    - تعداد گره‌ها
    - تعداد یال‌ها
    - پیچیدگی fusion_schema
    """
```

#### `evaluation/benchmark.py`

```python
class PredictionBenchmark:
    """بنچمارک پیش‌بینی"""
    
    def generate_random_numbers(self, seed, count) -> list[int]:
        """تولید اعداد تصادفی"""
    
    def compare_predictions(self, predicted, actual) -> dict:
        """
        مقایسه پیش‌بینی با واقعیت
        خروجی: BenchmarkResult
        """
```

#### `evaluation/external_trials.py`

```python
def run_external_trial(chromosome, system, questions) -> dict:
    """
    اجرای آزمایش خارجی
    - اجرای سیستم روی چند سوال
    - بررسی دقت پیش‌بینی
    """

class HistoricalBlindTest:
    """تست کور تاریخی"""

class HistoricalTestPacket:
    """بسته تست تاریخی"""
```

---

### ۷.۵ ماژول حافظه (`oracle/memory/`)

#### `memory/archive.py` - حافظه تکاملی

```python
class EvolutionaryMemory:
    """حافظه تکاملی مبتنی بر SQLite"""
    
    def __init__(self, db_path="evolution.db"):
        # جداول: generations, chromosomes, mutations
    
    def record_generation(self, gen, population, best):
        """ثبت نسل"""
    
    def get_best_chromosomes(self, n=10) -> list[dict]:
        """بهترین کروموزوم‌ها"""
    
    def get_generation_history(self, n=50) -> list[dict]:
        """تاریخچه نسل‌ها"""
```

#### `memory/lineage.py` - ردیابی خط سیر

```python
class LineageTracker:
    """ردیابی روابط والد-فرزندی"""
    
    def record_birth(self, child_id, parents=[], generation=0):
        """ثبت تولد"""
    
    def get_parents(self, id) -> list[str]
    def get_children(self, id) -> list[str]
    def get_ancestors(self, id, depth) -> list[str]
```

#### `memory/mutation_bank.py` - بانک جهش‌ها

```python
class MutationBank:
    """ذخیره الگوهای جهش موفق"""
    
    def record(self, mutation_type, chromosome_id, success, fitness_delta):
        """ثبت جهش"""
    
    def get_best_mutations(self, n=10) -> list[dict]:
        """بهترین جهش‌ها"""
```

#### `memory/fitness_history.py` - تاریخچه fitness

```python
class FitnessHistory:
    """پیگیری fitness در طول زمان"""
    
    def record(self, chromosome_id, generation, scores):
        """ثبت امتیاز"""
    
    def get_history(self, chromosome_id) -> list[dict]:
        """تاریخچه"""
```

#### `memory/experiment_ledger.py` - دفتر آزمایش‌ها

```python
class ExperimentLedger:
    """ثبت آزمایش‌ها"""
    
    def log_experiment(self, name, params, results):
        """ثبت آزمایش"""
    
    def get_experiments(self, name=None) -> list[dict]:
        """دریافت آزمایش‌ها"""
```

#### `memory/oracle_registry.py` - رجیستری oracle

```python
class OracleRegistry]:
    """نقشه سوالات به خروجی‌های گذشته"""
    
    def register(self, question, output):
        """ثبت خروجی"""
    
    def lookup(self, question) -> OracleOutput:
        """جستجو"""
    
    def get_similar(self, question, n=5) -> list:
        """سوالات مشابه"""
```

#### `memory/chromosome_archive.py`

```python
class ChromosomeArchive:
    """آرشیو بهترین کروموزوم‌ها"""
    
    def save(self, chromosome):
        """ذخیره"""
    
    def load(self, chromosome_id) -> Chromosome
    def get_top(self, n=10) -> list[Chromosome]
```

#### `memory/generational_memory.py`

```python
class GenerationalMemory:
    """حافظه نسلی - بارگذاری/تزریق الگوها"""
    
    def get_injection_candidates(self, n=5) -> list[Chromosome]
    def record_successful(self, chromosome)
```

#### `memory/graph_store.py`

```python
class GraphStore:
    """ذخیره گرافی روابط سیستم‌ها"""
    
    def add_node(self, id, attrs)
    def add_edge(self, src, dst)
    def get_neighbors(self, id)
    def shortest_path(self, src, dst)
```

#### `memory/symbolic_archive.py`

```python
class SymbolicArchive:
    """آرشیو خروجی سیستم‌های نمادین"""
    
    def archive(self, output)
    def get_by_system(self, system_id) -> list[SymbolicOutput]
```

---

### ۷.۶ ماژول ترکیب (`oracle/fusion/`)

#### `fusion/symbolic_fusion.py`

```python
class SymbolicFusionLayer:
    """ترکیب حالات نمادین از سیستم‌های مختلف"""
    
    def fuse(self, symbolic_outputs) -> dict:
        """
        ترکیب:
        - ادغام کلیدها
        - ترجیح مقادیر غالب
        """
```

#### `fusion/numeric_fusion.py`

```python
class NumericFusionLayer:
    """ترکیب بردارهای عددی"""
    
    def fuse(self, numeric_outputs) -> list[float]:
        """
        روش‌ها:
        - میانگین وزنی
        - میانه
        - بیشینه
        """
```

#### `fusion/graph_fusion.py`

```python
class GraphFusionLayer:
    """ترکیب از طریق عملیات گرافی"""
    
    def fuse(self, system_outputs) -> dict
```

#### `fusion/evolved_fusion.py`

```python
class EvolvedFusion:
    """ترکیب تکاملی - الگوی ترکیب توسط GA بهینه شده"""
    
    def fuse(self, chromosome, system_outputs) -> dict
```

#### `fusion/mapping.py`

```python
class MappingSchema:
    """نگاشت خروجی سیستم‌ها به فضای خروجی یکپارچه"""
    
    def apply(self, system_outputs) -> dict
```

---

### ۷.۷ ماژول رابط (`oracle/interface/`)

#### `interface/question.py`

```python
class QuestionParser:
    """تحلیلگر سوال"""
    
    def parse(self, question) -> dict:
        """
        خروجی:
        {
            "normalized_text": str,
            "domain": str,
            "keywords": list[str]
        }
        """
```

#### `interface/normalization.py`

```python
def normalize_text(text) -> str
def normalize_question(text) -> dict
```

#### `interface/schemas.py`

اسکیمای اعتبارسنجی ورودی/خروجی.

---

### ۷.۸ ماژول خروجی (`oracle/output/`)

#### `output/oracle_output.py`

```python
@dataclass
class OracleOutput:
    """خروجی نهایی oracle"""
    answer: str                     # پاسخ
    confidence: float               # اطمینان (0.0 - 1.0)
    dominant_systems: list[str]     # سیستم‌های غالب
    numeric_projections: list[float] # بردارهای عددی
    symbolic_states: dict           # حالات نمادین
    explanation: str                # توضیح
    disclaimer: str                 # سلب مسئولیت
    metadata: dict                  # فراداده
    
    def to_dict(self) -> dict
    def to_json(self) -> str
```

#### `output/explanation.py`

```python
class ExplanationBuilder:
    """سازنده توضیحات انسان‌خوانا"""
    
    def build(self, output) -> str:
        """
        تولید توضیح شامل:
        - هماهنگی ساختاری
        - پایداری پاسخ
        - نوآوری
        """
```

#### `output/report.py`

```python
class ReportGenerator:
    """تولید گزارش"""
    
    def generate(self, output, format='text') -> str:
        """
        فرمت‌ها:
        - text: متن ساده
        - html: HTML
        - markdown: Markdown
        - json: JSON
        """
```

#### `output/visualization.py`

```python
class Visualizer:
    """تجسم‌سازی"""
    
    def plot_fitness(self, history) -> None     # نمودار fitness
    def plot_systems(self, output) -> None     # نمودار سیستم‌ها
```

---

### ۷.۹ ماژول اجرا (`oracle/runtime/`)

#### `runtime/executor.py` - هماهنگ‌کننده اصلی

```python
class OraclePipeline:
    """هماهنگ‌کننده اصلی سیستم"""
    
    def __init__(self, config=None):
        self.encoder = EntropyEncoder()
        self.fitness_evaluator = FitnessEvaluator()
        self.fusion_layers = {...}
        self.cache = ResultCache()
    
    def ask(self, question, generations=200, engine='deap') -> OracleOutput:
        """
        سوال کامل
        
        مراحل:
        1. رمزگذاری آنتروپی
        2. تکامل جمعیت
        3. اجرای بهترین کروموزوم
        4. ترکیب خروجی‌ها
        5. ساخت توضیح
        6. ساخت خروجی نهایی
        """
    
    def ask_tree(self, question, generations=200) -> OracleOutput:
        """سوال با موتور GP"""
    
    def list_systems(self) -> list[str]
    def compute_system(self, id, packet) -> SymbolicOutput
```

#### `runtime/pipeline.py`

```python
class OraclePipelineExecutor:
    """لوله‌کشی پایین‌سطح"""
    
    def execute(self, question, generations, engine):
        """
        encode → evolve → fuse → explain → output
        """
```

#### `runtime/cache.py`

```python
class ResultCache:
    """کش LRU برای نتایج"""
    
    def get(self, key) -> OracleOutput
    def set(self, key, output)
    def has(self, key) -> bool
```

#### `runtime/sandbox.py`

```python
class SafeExecutor:
    """اجرای ایمن سیستم‌های نمادین"""
    
    def safe_compute(self, system, packet) -> SymbolicOutput:
        """اجرا با مدیریت خطا"""
```

---

### ۷.۱۰ ماژول نمادین (`oracle/symbolic/`)

#### `symbolic/base.py` - کلاس پایه

```python
@dataclass
class SymbolicOutput:
    """خروجی یک سیستم نمادین"""
    system_id: str
    subsystem: str
    symbolic_state: dict           # حالت نمادین
    numeric_projection: list[float] # بردار عددی
    structural_features: dict      # ویژگی‌های ساختاری
    confidence: float              # اطمینان
    metadata: dict

class SymbolicSystemWrapper(ABC):
    """کلاس پایه انتزاعی برای تمام سیستم‌ها"""
    
    @abstractmethod
    def compute(self, entropy_packet, params=None) -> SymbolicOutput:
        """محاسبه خروجی نمادین"""
```

#### `symbolic/registry.py` - رجیستری

```python
_registry: dict[str, type] = {}
_instances: dict[str, SymbolicSystemWrapper] = {}

@register_system(id="gematria", cls=GematriaWrapper, tags=["letter_number"])
class GematriaWrapper(SymbolicSystemWrapper): ...

def get_system(id) -> SymbolicSystemWrapper
def list_systems() -> list[str]
def compute_system(id, packet) -> SymbolicOutput
```

#### `symbolic/modifiable.py` - سیستم‌های قابل تغییر

```python
class SystemParameter:
    """پارامتر قابل تغییر"""
    name: str
    value: float
    param_type: str
    min_val: float
    max_val: float
    
    def mutate(self, intensity) -> SystemParameter

class SystemConfig:
    """پیکربندی سیستم"""
    system_id: str
    parameters: dict[str, SystemParameter]
    input_transform: str
    output_transform: str
    custom_formulas: list[dict]
    calculation_method: str
    combination_rules: list[dict]
    
    def mutate_params(self, intensity) -> SystemConfig

class ModifiableSystem:
    """سیستم قابل تغییر"""
    
    def __init__(self, wrapper, config):
        self.wrapper = wrapper
        self.config = config
    
    def compute(self, entropy_packet) -> SymbolicOutput:
        """اعمال فرمول‌ها و تبدیلات"""

class FormulaEngine:
    """موتور فرمول"""
    
    def random_formula(self, depth) -> str
    def mutate_formula(self, formula, intensity) -> str
    def evaluate_formula(self, formula, variables) -> float
```

---

## ۸. سیستم‌های نمادین

### ۸.۱ طالع‌بینی و تقویم (`symbolic/astrology/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| تقویم فارسی/هجری | `CalendarWrapper` | تبدیل تقویم جلالی، هجری، میلادی |
| طالع‌بینی وسترن | `WesternWrapper` | طالع‌بینی غربی |
| طالع‌بینی ودیک | `VedicWrapper` | طالع‌بینی هندی |
| Skyfield | `SkyfieldWrapper` | محاسبات نجومی دقیق |
| Yaegi Kundali | `YaegiKundaliWrapper` | کندالی |

### ۸.۲ سیستم‌های دودویی (`symbolic/binary/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| IChing | `IChingWrapper` | ای چینگ (64 هگزگرام) |
| جومانسی | `GeomancyWrapper` | جومانسی اسلامی (16.figure) |
| رمل | `RamlWrapper` | رمل عربی |
| IChingshifa | `IChingshifaWrapper` | ای چینگ شفا |

### ۸.۳ کارت‌ها (`symbolic/cards/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| تاروت | `TarotWrapper` | 78 کارت تاروت |
| رون‌ها | `RunesWrapper` | الفبای رون ( Elder Futhark) |
| لینورماند | `LenormandWrapper` | 36 کارت لینورماند |
| AI Tarot | `AITarotWrapper` | تاروت هوش مصنوعی |
| AI IChing | `AIIChingWrapper` | ای چینگ هوش مصنوعی |
| Tarot Oracle | `TarotOracleWrapper` | تاروت اوراکل |

### ۸.۴ شرقی (`symbolic/eastern/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| بازی (Four Pillars) | `BaziWrapper` | چهار ستون سرنوشت |
| زیویی | `ZiWeiWrapper` | ستاره بنفش |
| قیمن | `QiMenWrapper` | قیمن دون جیا |
| تقویم قمری | `LunarCalendarWrapper` | تقویم قمری چینی |
| Korean Saju | `KoreanSajuWrapper` | ساجو کره‌ای |
| Tianji Bazi | `TianjiBaziWrapper` | بازی تیانجی |
| Tianji Ziwei | `TianjiZiWeiWrapper` | زیویی تیانجی |
| Tianji Qimen | `TianjiQiMenWrapper` | قیمن تیانجی |
| Tianji Liuren | `TianjiLiurenWrapper` | لیورن تیانجی |

### ۸.۵ گماتریا و عددشناسی (`symbolic/gematria/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| عبجد | `GematriaWrapper` | گماتریا عربی |
| عبری | `HebrewGematriaWrapper` | گماتریا عبری |
| عبری پیشرفته | `HebrewAdvancedWrapper` | گماتریا عبری پیشرفته |
| انگلیسی | `EnglishGematriaWrapper` | گماتریا انگلیسی |
| عددشناسی | `NumerologyWrapper` | پیتاگوری |

### ۸.۶ مایا (`symbolic/mayan/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| Long Count | `LongCountWrapper` | تقویم بلند مایا |
| Tzolkin | `TzolkinWrapper` | تقویم مقدس مایا |
| Pohualli | `PohualliWrapper` | تقویم مدنی مایا |

### ۸.۷ رویا و فال (`symbolic/dreams/`, `symbolic/fortune_telling/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| نمادهای رویا | `DreamSymbolWrapper` | فرهنگ لغت نمادهای رویا |
| فال | `FortuneCore` | هسته فال‌گیری |
| اعداد مثلثی | `FigurateNumberWrapper` | اعداد مثلثی و فضایی |

### ۸.۸ عددی (`symbolic/numerical/`)

| سیستم | کلاس | توضیح |
|-------|------|-------|
| Figurate Plane | `FiguratePlaneWrapper` | اعداد مثلثی |
| Figurate Space | `FigurateSpaceWrapper` | اعداد فضایی |

---

## ۹. موتورهای تکاملی

### ۹.۱ موتورهای داخلی

#### GA (الگوریتم ژنتیک) - `deap_engine.py`

- **جمعیت**: 50 کروموزوم
- **نسل‌ها**: 200 پیش‌فرض
- **انتخاب**: Tournament + Elitism
- **تقاطع**: 5 نوع (یکنواخت، زیرگرافی، تمدنی، قانونی، حافظه‌ای)
- **جهش**: 7 نوع (پارامتری، ساختاری، تمدنی، بُعدی، قانونی، ضدارثباتی، عمیق)
- **ویژگی‌ها**: گسترش/هرس، ابداع قوانین، کنترل تنوع

#### GP (برنامه‌سازی ژنتیکی) - `gp_engine.py`

- **نمایش**: درختی (TreeGenome)
- **عملگرها**: +, -, *, /, sin, cos, log, exp, ...
- **ترمینال‌ها**: x, y, n, t, h, s, e, ...
- **عمق مаксیموم**: 10

#### NSGA-II (بهینه‌سازی چندهدفه) - `nsga_engine.py`

- **کتابخانه**: pymoo
- **اهداف**: هماهنگی ساختاری، نوآوری، پیچیدگی
- **مرتب‌سازی**: غیرتسلطی
- **فواصل شلوغی**: برای حفظ تنوع

### ۹.۲ موتورهای خارجی (۱۶ موتور)

هر موتور خارجی دارای ویژگی‌های زیر است:

- **تلاش برای استفاده** از کتابخانه خارجی
- **برگشت به حالت ایمن** در صورت عدم نصب
- **خروجی یکسان**: لیست بهترین کروموزوم‌ها

### ۹.۳ مدل جزیره‌ای

- **تعداد جزیره‌ها**: 4 (قابل تنظیم)
- **خانواده‌ها**: western, eastern, binary, letter_number, hybrid
- **مهاجرت**: هر 10 نسل
- **نرخ مهاجرت**: 10% جمعیت
- **توپولوژی**: حلقه‌ای

---

## ۱۰. سیستم ارزیابی

### ۱۰.۱ ابعاد fitness (9 بُعد)

| بُعد | وزن | توضیح |
|------|------|-------|
| `structural_coherence` | 0.15 | هماهنگی ساختار گراف |
| `symbolic_diversity` | 0.12 | تنوع سیستم‌های استفاده شده |
| `numerical_coherence` | 0.10 | هماهنگی بردارهای عددی |
| `information_density` | 0.08 | تراکم اطلاعات خروجی |
| `temporal_alignment` | 0.08 | هم‌راستایی با زمان |
| `complexity_penalty` | 0.07 | جریمه پیچیدگی بیش از حد |
| `novelty_bonus` | 0.05 | پاداش نوآوری |
| `prediction_accuracy` | 0.20 | دقت پیش‌بینی |
| `total_fitness` | - | مجموع وزنی |

### ۱۰.۲ آزمایش‌های خارجی

- **تست عدد تصادفی**: مقایسه پیش‌بینی با اعداد واقعی
- **تست کور تاریخی**: بررسی دقت روی رویدادهای تاریخی
- **آزمایش‌های چندسوالی**: اجرای سیستم روی مجموعه سوالات

---

## ۱۱. حافظه و ماندگاری

### ۱۱.۱ اجزای حافظه

| جزء | وظیفه | ذخیره‌سازی |
|------|--------|-----------|
| `EvolutionaryMemory` | تاریخچه نسل‌ها | SQLite |
| `ChromosomeArchive` | بهترین کروموزوم‌ها | فایل |
| `LineageTracker` | روابط والد-فرزندی | دیکشنری |
| `MutationBank` | الگوهای جهش موفق | دیکشنری |
| `FitnessHistory` | تاریخچه fitness | دیکشنری |
| `ExperimentLedger` | آزمایش‌ها | JSON |
| `OracleRegistry` | سوالات ↔ خروجی‌ها | دیکشنری |
| `GenerationalMemory` | الگوهای نسلی | لیست |
| `GraphStore` | روابط سیستم‌ها | networkx |
| `SymbolicArchive` | خروجی نمادین | دیکشنری |

### ۱۱.۲ جداول SQLite

```sql
-- جدول نسل‌ها
CREATE TABLE generations (
    id INTEGER PRIMARY KEY,
    generation INTEGER,
    avg_fitness REAL,
    best_fitness REAL,
    timestamp DATETIME
);

-- جدول کروموزوم‌ها
CREATE TABLE chromosomes (
    id TEXT PRIMARY KEY,
    generation INTEGER,
    fitness REAL,
    data BLOB,
    timestamp DATETIME
);

-- جدول جهش‌ها
CREATE TABLE mutations (
    id INTEGER PRIMARY KEY,
    chromosome_id TEXT,
    mutation_type TEXT,
    success BOOLEAN,
    fitness_delta REAL,
    timestamp DATETIME
);
```

---

## ۱۲. پیکربندی

### ۱۲.۱ `config/settings.yaml`

```yaml
project:
  name: "Universal Algorithmic Oracle"
  version: "0.2.0"
  phase: "development"

paths:
  data_dir: "data"
  export_dir: "experiments"

entropy:
  hash_algorithm: "sha256"
  bit_stream_length: 256
```

### ۱۲.۲ `config/evolution.yaml`

```yaml
population_size: 50
max_generations: 200
elite_count: 5

mutation:
  rate: 0.15
  types:
    - parameter
    - structural
    - civilization
    - dimensional

crossover:
  rate: 0.7
  types:
    - subgraph
    - civilization
    - rule

engine:
  default: deap
  available:
    - deap
    - pymoo
    - pygad
    - nevergrad
    - mealpy
    - evosax
    - niapy
    - pyswarm
    - neat-python
```

### ۱۲.۳ `config/fitness.yaml`

```yaml
weights:
  structural_coherence: 0.15
  symbolic_diversity: 0.12
  numerical_coherence: 0.10
  information_density: 0.08
  temporal_alignment: 0.08
  complexity_penalty: 0.07
  novelty_bonus: 0.05
  prediction_accuracy: 0.20

pure_entropy_test:
  enabled: true
  test_count: 100

historical_blind_test:
  enabled: true
  test_packets: 50
```

---

## ۱۳. تست‌ها

### اجرای تمام تست‌ها

```bash
python tests/test_all.py
```

### تست‌های موجود

| فایل | تست‌ها |
|------|--------|
| `test_all.py` | یکپارچه کامل (9 تست) |
| `test_entropy.py` | آنتروپی، تقویم، ماتریس |
| `test_genome.py` | ژن، کروموزوم، گراف ژنوم |
| `test_wrappers.py` | تمام سیستم‌های نمادین |
| `test_fitness.py` | ارزیاب fitness |
| `test_memory.py` | حافظه، بانک جهش، آزمایش، خط سیر |
| `test_mutation.py` | جهش پارامتری و ساختاری |
| `test_crossover.py` | تقاطع یکنواخت |

### خروجی تست‌ها

```
[PASS] test_entropy_encoder
[PASS] test_gematria_wrapper
[PASS] test_iching_wrapper
[PASS] test_geomancy_wrapper
[PASS] test_calendar_wrapper
[PASS] test_chromosome
[PASS] test_fitness_evaluator
[PASS] test_evolutionary_engine
[PASS] test_full_pipeline
=== ALL TESTS PASSED ===
```

---

## ۱۴. نمودار جریان داده

### جریان اصلی

```
                    ┌─────────────────┐
                    │   سوال کاربر     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Entropy Encoder  │
                    │  (SHA-256, Bit)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  EntropyPacket   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Population   │ │ Island 1    │ │ Island 2    │
    │ Manager      │ │ (Western)   │ │ (Eastern)   │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────────────────────────────────────┐
    │              Evolution Loop                  │
    │  ┌────────────────────────────────────────┐ │
    │  │  1. Fitness Evaluation (9D)            │ │
    │  │  2. Tournament Selection               │ │
    │  │  3. Crossover (5 types)                │ │
    │  │  4. Mutation (7 types)                 │ │
    │  │  5. Expansion/Pruning                  │ │
    │  │  6. Rule Invention                     │ │
    │  │  7. Diversity Control                  │ │
    │  │  8. Memory Recording                   │ │
    │  └────────────────────────────────────────┘ │
    └──────────────────────┬──────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Best Chromosome  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Execute on EP    │
                  │ (Topo Sort)      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Fusion Layers    │
                  │ (Num+Sym+Graph)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Explanation      │
                  │ Builder          │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ OracleOutput     │
                  │ (Answer+Conf)    │
                  └─────────────────┘
```

### جریان جزیره‌ای

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Island 1  │◄──►│ Island 2  │◄──►│ Island 3  │◄──►│ Island 4  │
│ (Western) │    │ (Eastern) │    │ (Binary)  │    │ (Hybrid)  │
└─────┬────┘    └─────┬────┘    └─────┬────┘    └─────┬────┘
      │               │               │               │
      │    Migration (every 10 gen)   │               │
      └───────────────┼───────────────┼───────────────┘
                      │               │
                      ▼               ▼
              ┌───────────────────────────────┐
              │       Global Best Selection    │
              └───────────────────────────────┘
```

---

## ۱۵. مشکلات شناخته‌شده

1. **وابستگی‌های اختیاری**: برخی موتورهای خارجی ممکن است نصب نباشند (حالت fallback فعال)
2. **عملکرد**: اجرای کامل تکامل با 200 نسل ممکن است چند دقیقه طول بکشد
3. **حافظه**: برای سوالات پیچیده، حافظه ممکن است زیاد شود
4. **پایتون 3.14**: برخی وابستگی‌ها ممکن است با پایتون 3.14 سازگار نباشند

---

## ۱۶. نقشه راه آینده

- [ ] رابط وب (Flask/FastAPI)
- [ ] پشتیبانی از API خارجی (OpenAI, Anthropic)
- [ ] بهینه‌سازی عملکرد (parallel processing)
- [ ] تست‌های بیشتر
- [ ] مستندات API
- [ ] نمودارهای تعاملی
- [ ] پشتیبانی از چند زبان
- [ ] بهینه‌سازی حافظه
- [ ] مدل‌های یادگیری عمیق
- [ ] رابط گرافیکی (GUI)

---

## مجوز

Business Source License 1.1 (BSL-1.1)

---

**تاریخ آخرین به‌روزرسانی**: ژوئن 2026
**نسخه**: 0.2.0
**وضعیت**: در حال توسعه
