-- 基因表达系列表
CREATE TABLE IF NOT EXISTS gse (
    id INTEGER PRIMARY KEY,
    accession TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    organism TEXT,
    platform TEXT,
    sample_count INTEGER,
    release_date TEXT,
    updated_date TEXT,
    description TEXT
);

-- 样本表
CREATE TABLE IF NOT EXISTS gsm (
    id INTEGER PRIMARY KEY,
    accession TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    gse_accession TEXT,
    organism TEXT,
    source TEXT,
    characteristics TEXT,
    treatment TEXT,
    FOREIGN KEY(gse_accession) REFERENCES gse(accession)
);

-- 插入示例GSE数据
INSERT OR IGNORE INTO gse (accession, title, organism, platform, sample_count, release_date, description) 
VALUES 
('GSE10000', 'Mouse liver expression profile', 'Mus musculus', 'Affymetrix Mouse Genome 430 2.0', 12, '2020-01-15', 'This dataset contains gene expression profiles from mouse liver samples under different conditions.'),
('GSE20000', 'Human brain single-cell RNA-seq', 'Homo sapiens', 'Illumina HiSeq 2500', 1500, '2021-05-20', 'Single-cell RNA sequencing of human brain cells to study cellular heterogeneity and identify cell types.');

-- 插入示例GSM数据
INSERT OR IGNORE INTO gsm (accession, title, gse_accession, organism, source, characteristics, treatment)
VALUES 
('GSM250001', 'Liver sample 1 - control', 'GSE10000', 'Mus musculus', 'liver tissue', 'male, 12 weeks', 'control'),
('GSM250002', 'Liver sample 2 - treated', 'GSE10000', 'Mus musculus', 'liver tissue', 'male, 12 weeks', 'drug treatment'),
('GSM250003', 'Liver sample 3 - control', 'GSE10000', 'Mus musculus', 'liver tissue', 'female, 12 weeks', 'control'),
('GSM500001', 'Brain cell 1 - neuron', 'GSE20000', 'Homo sapiens', 'brain tissue', 'cortex, neuron', 'none'),
('GSM500002', 'Brain cell 2 - astrocyte', 'GSE20000', 'Homo sapiens', 'brain tissue', 'cortex, astrocyte', 'none');

-- 创建索引以加速查询
CREATE INDEX IF NOT EXISTS idx_gse_accession ON gse(accession);
CREATE INDEX IF NOT EXISTS idx_gsm_accession ON gsm(accession);
CREATE INDEX IF NOT EXISTS idx_gsm_gse_accession ON gsm(gse_accession); 