'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Shield, CheckCircle2, XCircle, AlertCircle, RefreshCw,
  Zap, Thermometer, Scale, TrendingUp, Link2, Lock, Hash
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

// ============================================
// TYPES
// ============================================

interface LawStatus {
  id: number;
  name: string;
  statement: string;
  satisfied: boolean;
  details: Record<string, any>;
}

interface EnforcementResult {
  allLawsSatisfied: boolean;
  lawsSatisfied: {
    quadraticInvariance: boolean;
    boundaryEntropy: boolean;
    auditableGovernance: boolean;
    optimizedEfficiency: boolean;
  };
  law1QuadraticInvariance: any;
  law2BoundaryEntropy: any;
  law3AuditableGovernance: any;
  law4OptimizedEfficiency: any;
  timestamp: number;
}

// ============================================
// LAW CARD COMPONENT
// ============================================

function LawCard({
  id,
  name,
  statement,
  satisfied,
  details,
  isExpanded,
  onToggle
}: {
  id: number;
  name: string;
  statement: string;
  satisfied: boolean;
  details: Record<string, any>;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const icons = [Zap, Thermometer, Scale, TrendingUp];
  const Icon = icons[id - 1] || Shield;
  
  return (
    <Card className={`${satisfied ? 'border-green-500/50' : 'border-red-500/50'}`}>
      <CardHeader className="pb-2 cursor-pointer" onClick={onToggle}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${satisfied ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
              <Icon className={`h-5 w-5 ${satisfied ? 'text-green-600' : 'text-red-600'}`} />
            </div>
            <div>
              <CardTitle className="text-sm">Law {id}: {name}</CardTitle>
              <CardDescription className="text-xs">{statement.slice(0, 50)}...</CardDescription>
            </div>
          </div>
          <Badge variant={satisfied ? 'default' : 'destructive'}>
            {satisfied ? 'SATISFIED' : 'VIOLATED'}
          </Badge>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="pt-2">
          <div className="space-y-2 text-xs">
            <div>
              <Label className="text-muted-foreground">Formal Statement</Label>
              <p className="mt-1 font-mono bg-muted p-2 rounded">{statement}</p>
            </div>
            
            <Separator />
            
            <div>
              <Label className="text-muted-foreground">Details</Label>
              <pre className="mt-1 bg-muted p-2 rounded overflow-auto max-h-[200px]">
                {JSON.stringify(details, null, 2)}
              </pre>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// ============================================
// VERIFICATION PANEL
// ============================================

function VerificationPanel() {
  const [coords, setCoords] = useState('0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5');
  const [results, setResults] = useState<{
    snapIdempotency: any;
    weylReversibility: any;
    quadraticForm: any;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  
  const runVerification = useCallback(async () => {
    setLoading(true);
    try {
      const [snapRes, weylRes, qfRes] = await Promise.all([
        fetch(`/api/laws?action=verify-snap-idempotency&coords=${coords}`),
        fetch(`/api/laws?action=verify-weyl-reversibility&coords=${coords}`),
        fetch(`/api/laws?action=quadratic-form&coords=${coords}`)
      ]);
      
      const snapData = await snapRes.json();
      const weylData = await weylRes.json();
      const qfData = await qfRes.json();
      
      setResults({
        snapIdempotency: snapData,
        weylReversibility: weylData,
        quadraticForm: qfData
      });
    } catch (error) {
      toast.error('Verification failed');
    } finally {
      setLoading(false);
    }
  }, [coords]);
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Lock className="h-4 w-4" />
          Law 1 Verification
        </CardTitle>
        <CardDescription>Test quadratic invariance, snap idempotency, Weyl reversibility</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label className="text-xs text-muted-foreground">8D Coordinates (comma-separated)</Label>
          <div className="flex gap-2 mt-1">
            <Input
              value={coords}
              onChange={(e) => setCoords(e.target.value)}
              placeholder="x1,x2,x3,x4,x5,x6,x7,x8"
              className="font-mono text-xs"
            />
            <Button onClick={runVerification} disabled={loading} size="sm">
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : 'Verify'}
            </Button>
          </div>
        </div>
        
        {results && (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2">
              <div className="p-3 bg-muted rounded text-center">
                <div className="text-xs text-muted-foreground mb-1">Snap Idempotent</div>
                {results.snapIdempotency.isIdempotent ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500 mx-auto" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 mx-auto" />
                )}
                <div className="text-[10px] text-muted-foreground mt-1">
                  dist: {results.snapIdempotency.distance?.toExponential(2)}
                </div>
              </div>
              
              <div className="p-3 bg-muted rounded text-center">
                <div className="text-xs text-muted-foreground mb-1">Weyl Reversible</div>
                {results.weylReversibility.allReversible ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500 mx-auto" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500 mx-auto" />
                )}
                <div className="text-[10px] text-muted-foreground mt-1">
                  max err: {results.weylReversibility.maxError?.toExponential(2)}
                </div>
              </div>
              
              <div className="p-3 bg-muted rounded text-center">
                <div className="text-xs text-muted-foreground mb-1">Q(x)</div>
                <div className="text-lg font-bold">{results.quadraticForm.quadraticForm?.toFixed(4)}</div>
                <div className="text-[10px] text-muted-foreground">
                  {Math.abs(results.quadraticForm.quadraticForm - 2) < 0.01 ? '≈ E8 norm²' : 'non-E8'}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// RECEIPT CHAIN PANEL
// ============================================

function ReceiptChainPanel() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/laws?action=receipt-chain');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching receipt chain:', error);
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);
  
  const createTestReceipt = async () => {
    try {
      const response = await fetch('/api/laws', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create-receipt',
          prevState: [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
          newState: [1, 0, 0, 0, 0, 0, 0, 0],
          principal: 'test-controller',
          invariantChecks: [
            { invariantName: 'QUADRATIC_FORM', passed: true, message: 'Q(x) = 2.0' }
          ]
        })
      });
      
      const data = await response.json();
      if (data.added) {
        toast.success('Receipt added to chain');
        fetchStats();
      } else {
        toast.error('Failed to add receipt');
      }
    } catch (error) {
      toast.error('Failed to create receipt');
    }
  };
  
  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 flex items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm flex items-center gap-2">
              <Link2 className="h-4 w-4" />
              Receipt Chain (Law 2)
            </CardTitle>
            <CardDescription>Hash-chained boundary event records</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={createTestReceipt}>
            Add Test Receipt
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {stats && (
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-muted rounded">
              <div className="text-2xl font-bold">{stats.stats?.receiptCount || 0}</div>
              <div className="text-xs text-muted-foreground">Receipts</div>
            </div>
            <div className="text-center p-3 bg-muted rounded">
              <div className="text-2xl font-bold">{(stats.stats?.totalEntropy || 0).toFixed(4)}</div>
              <div className="text-xs text-muted-foreground">Total ΔS</div>
            </div>
            <div className="text-center p-3 bg-muted rounded">
              <div className="text-2xl font-bold">{stats.stats?.uniquePrincipals || 0}</div>
              <div className="text-xs text-muted-foreground">Principals</div>
            </div>
            <div className="text-center p-3 bg-muted rounded">
              <Badge variant={stats.verification?.isValid ? 'default' : 'destructive'}>
                {stats.verification?.isValid ? 'VALID' : 'INVALID'}
              </Badge>
              <div className="text-xs text-muted-foreground mt-1">Chain Status</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// STRUCTURAL DIVIDEND PANEL
// ============================================

function StructuralDividendPanel() {
  const [n, setN] = useState(1000);
  const [results, setResults] = useState<any>(null);
  
  const measureAll = useCallback(async () => {
    try {
      const [e8Res, mdhgRes, lanesRes] = await Promise.all([
        fetch(`/api/laws?action=structural-dividend&type=e8&n=${n}`),
        fetch(`/api/laws?action=structural-dividend&type=mdhg&n=${n}`),
        fetch(`/api/laws?action=structural-dividend&type=hashlanes&n=${n}`)
      ]);
      
      const [e8, mdhg, lanes] = await Promise.all([
        e8Res.json(),
        mdhgRes.json(),
        lanesRes.json()
      ]);
      
      setResults({ e8, mdhg, lanes });
    } catch (error) {
      console.error('Error measuring structural dividend:', error);
    }
  }, [n]);
  
  // Load initial data on mount
  useEffect(() => {
    measureAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Structural Dividend (Law 4)
        </CardTitle>
        <CardDescription>SD = C_naive - C_CQE ≥ 0</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Label className="text-xs text-muted-foreground">Scale (n):</Label>
          <Input
            type="number"
            value={n}
            onChange={(e) => setN(parseInt(e.target.value) || 100)}
            className="w-24"
          />
          <Button onClick={measureAll} size="sm">Measure</Button>
        </div>
        
        {results && (
          <div className="space-y-3">
            <div className="p-3 bg-muted rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium">E8 Snap</span>
                <Badge variant={results.e8.lawSatisfied ? 'default' : 'destructive'}>
                  SD = {results.e8.structuralDividend?.toFixed(2)}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                Naive: {results.e8.costNaive} → CQE: {results.e8.costCQE?.toFixed(2)}
              </div>
            </div>
            
            <div className="p-3 bg-muted rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium">MDHG Cache</span>
                <Badge variant={results.mdhg.lawSatisfied ? 'default' : 'destructive'}>
                  SD = {results.mdhg.structuralDividend?.toFixed(2)}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                Naive: {results.mdhg.costNaive?.toFixed(2)} → CQE: {results.mdhg.costCQE?.toFixed(2)}
              </div>
            </div>
            
            <div className="p-3 bg-muted rounded">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium">Hash Lanes</span>
                <Badge variant={results.lanes.lawSatisfied ? 'default' : 'destructive'}>
                  SD = {results.lanes.structuralDividend?.toFixed(2)}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                Naive: {results.lanes.costNaive} → CQE: {results.lanes.costCQE?.toFixed(2)}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// GOVERNANCE STATE MACHINE PANEL
// ============================================

function GovernanceStateMachinePanel() {
  const [currentState, setCurrentState] = useState<string>('draft');
  const [evidence, setEvidence] = useState<number>(0.5);
  const [totalEvidence, setTotalEvidence] = useState<number>(0);
  
  const states = ['draft', 'explore', 'validated', 'replicated', 'archived'];
  const stateColors: Record<string, string> = {
    draft: 'bg-gray-100 dark:bg-gray-900/20 text-gray-700',
    explore: 'bg-blue-100 dark:bg-blue-900/20 text-blue-700',
    validated: 'bg-green-100 dark:bg-green-900/20 text-green-700',
    replicated: 'bg-purple-100 dark:bg-purple-900/20 text-purple-700',
    archived: 'bg-amber-100 dark:bg-amber-900/20 text-amber-700'
  };
  
  const advanceState = async (targetState?: string) => {
    try {
      const response = await fetch('/api/laws', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'advance-governance',
          currentState,
          evidence,
          targetState
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setCurrentState(data.newState);
        setTotalEvidence(prev => prev + evidence);
        toast.success(`Advanced to ${data.newState}`);
      } else {
        toast.error(data.reason);
      }
    } catch (error) {
      toast.error('Failed to advance state');
    }
  };
  
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Scale className="h-4 w-4" />
          Governance State Machine (Law 3)
        </CardTitle>
        <CardDescription>draft → explore → validated → replicated → archived</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          {states.map((state, i) => (
            <div key={state} className="flex items-center">
              <div className={`px-3 py-1 rounded text-xs font-medium ${
                state === currentState 
                  ? stateColors[state] + ' ring-2 ring-primary'
                  : 'bg-muted text-muted-foreground'
              }`}>
                {state}
              </div>
              {i < states.length - 1 && (
                <div className="w-4 h-px bg-muted-foreground/30" />
              )}
            </div>
          ))}
        </div>
        
        <Separator />
        
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Label className="text-xs text-muted-foreground">Evidence to Add</Label>
            <Input
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={evidence}
              onChange={(e) => setEvidence(parseFloat(e.target.value) || 0)}
              className="mt-1"
            />
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">{(totalEvidence * 100).toFixed(0)}%</div>
            <div className="text-xs text-muted-foreground">Total Evidence</div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button onClick={() => advanceState()} className="flex-1">
            Auto-Advance
          </Button>
          {currentState !== 'archived' && (
            <Button 
              variant="outline" 
              onClick={() => advanceState(states[states.indexOf(currentState) + 1])}
            >
              Force Next
            </Button>
          )}
        </div>
        
        <div className="text-xs text-muted-foreground">
          Threshold: 80% evidence required for explore → validated transition
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================
// MAIN PANEL
// ============================================

export default function FoundationalLawsPanel() {
  const [expandedLaw, setExpandedLaw] = useState<number | null>(null);
  const [enforcementResult, setEnforcementResult] = useState<EnforcementResult | null>(null);
  
  const laws = [
    {
      id: 1,
      name: 'Quadratic Invariance',
      statement: 'Q(T(x)) = Q(x) for lawful transformations T. The quadratic form invariant I(Q(x)) is preserved under all lawful transformations.',
      satisfied: enforcementResult?.lawsSatisfied.quadraticInvariance ?? true,
      details: enforcementResult?.law1QuadraticInvariance || {}
    },
    {
      id: 2,
      name: 'Boundary-Only Entropy',
      statement: 'ΔS(O_int) = 0 for internal operations. Entropy change ΔS(B) ≠ 0 only at boundary events ∂D.',
      satisfied: enforcementResult?.lawsSatisfied.boundaryEntropy ?? true,
      details: enforcementResult?.law2BoundaryEntropy || {}
    },
    {
      id: 3,
      name: 'Auditable Governance',
      statement: 'C(O, S_prev, S_new, Σ) = 1 iff operation O complies with schema set Σ. φ-probe resolves ambiguities deterministically.',
      satisfied: enforcementResult?.lawsSatisfied.auditableGovernance ?? true,
      details: enforcementResult?.law3AuditableGovernance || {}
    },
    {
      id: 4,
      name: 'Optimized Efficiency',
      statement: 'SD = C_naive - C_CQE ≥ 0. The CQE approach yields non-negative structural dividend through PSP gains.',
      satisfied: enforcementResult?.lawsSatisfied.optimizedEfficiency ?? true,
      details: enforcementResult?.law4OptimizedEfficiency || {}
    }
  ];
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            The Four Foundational Laws of CQE
          </CardTitle>
          <CardDescription>
            Axiomatic foundation of the Cartan Quadratic Equivalence framework
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <Badge 
              variant={laws.every(l => l.satisfied) ? 'default' : 'destructive'}
              className="text-sm py-1 px-3"
            >
              {laws.every(l => l.satisfied) ? 'ALL LAWS SATISFIED' : 'LAW VIOLATION DETECTED'}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {laws.filter(l => l.satisfied).length}/4 laws satisfied
            </span>
          </div>
          
          <div className="space-y-3">
            {laws.map(law => (
              <LawCard
                key={law.id}
                {...law}
                isExpanded={expandedLaw === law.id}
                onToggle={() => setExpandedLaw(expandedLaw === law.id ? null : law.id)}
              />
            ))}
          </div>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <VerificationPanel />
        <ReceiptChainPanel />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GovernanceStateMachinePanel />
        <StructuralDividendPanel />
      </div>
      
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Law Interconnections</CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground">
          <ul className="space-y-2">
            <li>• <strong>Quadratic Invariance</strong> provides the mathematical basis for Auditable Governance (verifying invariant preservation)</li>
            <li>• <strong>Boundary-Only Entropy</strong> ensures Auditable Governance has receipted evidence</li>
            <li>• <strong>Optimized Efficiency</strong> leverages both invariant properties and receipted boundaries for computational gains</li>
            <li>• All four laws are <strong>mutually reinforcing</strong> — violating one necessarily violates at least one other</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
