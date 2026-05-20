// SpeedLight Receipt System
// Cryptographic proof of controller execution with hash chains

import { createHash, randomBytes, createVerify } from 'crypto';

// ============================================
// TYPES
// ============================================

export interface SpeedLightReceipt {
  schemaVersion: number;
  timestampUtc: string;
  controller: string;
  stepId: string;
  paramsDigest?: string;
  prevReceiptHash?: string;
  receiptHash: string;
  artifactsMerkleRoot?: string;
  signingKeyId?: string;
  signatureB64?: string;
  governanceMode?: 'STRICT' | 'EXPLORE';
  governanceBypass: boolean;
  payload?: Record<string, any>;
}

export interface ArtifactDigest {
  relpath: string;
  sha256: string;
  bytes: number;
  mimeType?: string;
}

export interface ReceiptChain {
  chainId: string;
  headHash: string;
  tailHash: string;
  receiptCount: number;
  createdAt: string;
}

// ============================================
// CANONICAL JSON SERIALIZATION
// ============================================

/**
 * Canonical JSON serialization for deterministic hashing.
 * Sorts keys recursively and removes undefined values.
 */
export function canonicalJson(obj: any): string {
  if (obj === null) return 'null';
  if (obj === undefined) return 'null';
  if (typeof obj !== 'object') return JSON.stringify(obj);
  
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalJson).join(',') + ']';
  }
  
  const sortedKeys = Object.keys(obj).sort();
  const pairs = sortedKeys
    .filter(k => obj[k] !== undefined)
    .map(k => `"${k}":${canonicalJson(obj[k])}`);
  return '{' + pairs.join(',') + '}';
}

// ============================================
// HASH COMPUTATION
// ============================================

export function sha256(data: string | Buffer): string {
  return createHash('sha256').update(data).digest('hex');
}

export function hashReceipt(receipt: Omit<SpeedLightReceipt, 'receiptHash' | 'signatureB64'>): string {
  const canonical = canonicalJson({
    schemaVersion: receipt.schemaVersion,
    timestampUtc: receipt.timestampUtc,
    controller: receipt.controller,
    stepId: receipt.stepId,
    paramsDigest: receipt.paramsDigest,
    prevReceiptHash: receipt.prevReceiptHash,
    artifactsMerkleRoot: receipt.artifactsMerkleRoot,
    governanceMode: receipt.governanceMode,
    governanceBypass: receipt.governanceBypass,
    payload: receipt.payload,
  });
  return sha256(canonical);
}

// ============================================
// MERKLE TREE
// ============================================

export function computeMerkleRoot(digests: ArtifactDigest[]): string {
  if (digests.length === 0) {
    return sha256('empty_merkle_root');
  }
  
  // Sort by relpath for determinism
  const sorted = [...digests].sort((a, b) => a.relpath.localeCompare(b.relpath));
  
  // Create leaf nodes
  let nodes = sorted.map(d => sha256(`${d.relpath}:${d.sha256}:${d.bytes}`));
  
  // Build tree
  while (nodes.length > 1) {
    const nextLevel: string[] = [];
    for (let i = 0; i < nodes.length; i += 2) {
      if (i + 1 < nodes.length) {
        nextLevel.push(sha256(nodes[i] + nodes[i + 1]));
      } else {
        // Odd node - promote to next level
        nextLevel.push(nodes[i]);
      }
    }
    nodes = nextLevel;
  }
  
  return nodes[0];
}

// ============================================
// RECEIPT GENERATION
// ============================================

export class SpeedLightReceiptGenerator {
  private keyId: string;
  private secretKey: Buffer;
  private prevHash: string | null = null;
  private receiptCount: number = 0;
  
  constructor(keyId?: string) {
    this.keyId = keyId || `key_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    this.secretKey = randomBytes(32);
  }
  
  getKeySecret(): string {
    return this.secretKey.toString('hex');
  }
  
  getKeyId(): string {
    return this.keyId;
  }
  
  generateReceipt(
    controller: string,
    stepId: string,
    artifacts: ArtifactDigest[],
    options: {
      paramsDigest?: string;
      governanceMode?: 'STRICT' | 'EXPLORE';
      governanceBypass?: boolean;
      payload?: Record<string, any>;
    } = {}
  ): SpeedLightReceipt {
    const timestampUtc = new Date().toISOString().replace(/\.\d{3}/, '');
    
    // Compute merkle root
    const artifactsMerkleRoot = computeMerkleRoot(artifacts);
    
    // Create receipt without hash/signature
    const receiptWithoutHash: Omit<SpeedLightReceipt, 'receiptHash' | 'signatureB64'> = {
      schemaVersion: 1,
      timestampUtc,
      controller,
      stepId,
      paramsDigest: options.paramsDigest,
      prevReceiptHash: this.prevHash || undefined,
      artifactsMerkleRoot,
      signingKeyId: this.keyId,
      governanceMode: options.governanceMode || 'STRICT',
      governanceBypass: options.governanceBypass || false,
      payload: options.payload,
    };
    
    // Compute hash
    const receiptHash = hashReceipt(receiptWithoutHash);
    
    // Create HMAC-based signature (deterministic)
    const signatureInput = `${receiptHash}:${this.keyId}:${this.secretKey.toString('hex')}`;
    const signatureB64 = sha256(signatureInput);
    
    // Update chain state
    this.prevHash = receiptHash;
    this.receiptCount++;
    
    return {
      ...receiptWithoutHash,
      receiptHash,
      signatureB64,
    };
  }
  
  getChainState(): { headHash: string | null; receiptCount: number } {
    return {
      headHash: this.prevHash,
      receiptCount: this.receiptCount,
    };
  }
  
  reset(): void {
    this.prevHash = null;
    this.receiptCount = 0;
  }
}

// ============================================
// VERIFICATION
// ============================================

export function verifyReceiptSignature(
  receipt: SpeedLightReceipt,
  publicKeyPem: string
): boolean {
  if (!receipt.signatureB64 || !receipt.receiptHash) {
    return false;
  }
  
  try {
    const verify = createVerify('sha256');
    verify.update(receipt.receiptHash);
    verify.end();
    return verify.verify(publicKeyPem, Buffer.from(receipt.signatureB64, 'base64'));
  } catch {
    return false;
  }
}

export function verifyReceiptHash(receipt: SpeedLightReceipt): boolean {
  const computed = hashReceipt({
    schemaVersion: receipt.schemaVersion,
    timestampUtc: receipt.timestampUtc,
    controller: receipt.controller,
    stepId: receipt.stepId,
    paramsDigest: receipt.paramsDigest,
    prevReceiptHash: receipt.prevReceiptHash,
    artifactsMerkleRoot: receipt.artifactsMerkleRoot,
    governanceMode: receipt.governanceMode,
    governanceBypass: receipt.governanceBypass,
    payload: receipt.payload,
  });
  return computed === receipt.receiptHash;
}

export function verifyReceiptChain(receipts: SpeedLightReceipt[]): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (receipts.length === 0) {
    return { valid: true, errors: [] };
  }
  
  // Sort by timestamp
  const sorted = [...receipts].sort((a, b) => 
    a.timestampUtc.localeCompare(b.timestampUtc)
  );
  
  let prevHash: string | null = null;
  
  for (let i = 0; i < sorted.length; i++) {
    const receipt = sorted[i];
    
    // Verify hash
    if (!verifyReceiptHash(receipt)) {
      errors.push(`Receipt ${i}: hash verification failed`);
    }
    
    // Verify chain linkage
    if (i === 0) {
      if (receipt.prevReceiptHash !== undefined && receipt.prevReceiptHash !== null) {
        errors.push(`Receipt ${i}: first receipt should not have prevReceiptHash`);
      }
    } else {
      if (receipt.prevReceiptHash !== prevHash) {
        errors.push(`Receipt ${i}: chain linkage broken`);
      }
    }
    
    prevHash = receipt.receiptHash;
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

// ============================================
// EXPORT BUNDLE
// ============================================

export interface ExportBundleManifest {
  version: number;
  createdAt: string;
  files: Array<{
    arcname: string;
    sha256: string;
    bytes: number;
  }>;
  ledgerSha256: string;
  metaSha256: string;
  chainHeadHash: string;
  totalReceipts: number;
}

export function createExportBundleManifest(
  receipts: SpeedLightReceipt[],
  artifacts: ArtifactDigest[]
): ExportBundleManifest {
  const chainState = verifyReceiptChain(receipts);
  
  return {
    version: 1,
    createdAt: new Date().toISOString(),
    files: artifacts.map(a => ({
      arcname: `artifacts/${a.relpath}`,
      sha256: a.sha256,
      bytes: a.bytes,
    })),
    ledgerSha256: sha256(receipts.map(r => r.receiptHash).join('\n')),
    metaSha256: sha256(canonicalJson({ receiptCount: receipts.length })),
    chainHeadHash: receipts.length > 0 ? receipts[receipts.length - 1].receiptHash : '',
    totalReceipts: receipts.length,
  };
}
