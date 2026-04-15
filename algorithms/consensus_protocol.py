"""
Algorithm 86: Consensus Protocol

- Nodes propose value
- Raft/Paxos consensus
- Fast leader election
- Log replication
- Consistency guaranteed
"""

import time
import random
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    """A single entry in the Raft log."""
    term: int
    index: int
    command: str
    data: dict = field(default_factory=dict)


@dataclass
class VoteRequest:
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


@dataclass
class VoteResponse:
    term: int
    vote_granted: bool
    voter_id: str


@dataclass
class AppendEntriesRequest:
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: list
    leader_commit: int


@dataclass
class AppendEntriesResponse:
    term: int
    success: bool
    node_id: str
    match_index: int = 0


class RaftNode:
    """A node implementing the Raft consensus protocol."""

    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers  # list of peer node_ids
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.last_applied = 0

        # Leader-specific state
        self.next_index = {}
        self.match_index = {}

        # Timing
        self.last_heartbeat = time.time()
        self.election_timeout = random.uniform(1.5, 3.0)

    def request_vote(self, request):
        """Handle a vote request from a candidate."""
        if request.term < self.current_term:
            return VoteResponse(
                term=self.current_term,
                vote_granted=False,
                voter_id=self.node_id,
            )

        if request.term > self.current_term:
            self.current_term = request.term
            self.state = NodeState.FOLLOWER
            self.voted_for = None

        # Grant vote if we haven't voted or already voted for this candidate
        if self.voted_for is None or self.voted_for == request.candidate_id:
            last_log_term = self.log[-1].term if self.log else 0
            last_log_index = len(self.log) - 1

            log_ok = (
                request.last_log_term > last_log_term or
                (request.last_log_term == last_log_term and
                 request.last_log_index >= last_log_index)
            )

            if log_ok:
                self.voted_for = request.candidate_id
                self.last_heartbeat = time.time()
                return VoteResponse(
                    term=self.current_term,
                    vote_granted=True,
                    voter_id=self.node_id,
                )

        return VoteResponse(
            term=self.current_term,
            vote_granted=False,
            voter_id=self.node_id,
        )

    def append_entries(self, request):
        """Handle AppendEntries RPC (heartbeat or log replication)."""
        if request.term < self.current_term:
            return AppendEntriesResponse(
                term=self.current_term,
                success=False,
                node_id=self.node_id,
            )

        self.current_term = request.term
        self.state = NodeState.FOLLOWER
        self.last_heartbeat = time.time()

        # Check log consistency
        if request.prev_log_index >= 0:
            if request.prev_log_index >= len(self.log):
                return AppendEntriesResponse(
                    term=self.current_term,
                    success=False,
                    node_id=self.node_id,
                )
            if self.log[request.prev_log_index].term != request.prev_log_term:
                self.log = self.log[:request.prev_log_index]
                return AppendEntriesResponse(
                    term=self.current_term,
                    success=False,
                    node_id=self.node_id,
                )

        # Append new entries
        for entry in request.entries:
            idx = entry.index
            if idx < len(self.log):
                if self.log[idx].term != entry.term:
                    self.log = self.log[:idx]
                    self.log.append(entry)
            else:
                self.log.append(entry)

        if request.leader_commit > self.commit_index:
            self.commit_index = min(
                request.leader_commit,
                len(self.log) - 1 if self.log else 0,
            )

        return AppendEntriesResponse(
            term=self.current_term,
            success=True,
            node_id=self.node_id,
            match_index=len(self.log) - 1 if self.log else 0,
        )

    def start_election(self):
        """Start a leader election."""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.last_heartbeat = time.time()

        last_log_term = self.log[-1].term if self.log else 0
        last_log_index = len(self.log) - 1

        return VoteRequest(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=last_log_index,
            last_log_term=last_log_term,
        )

    def become_leader(self):
        """Become the leader after winning election."""
        self.state = NodeState.LEADER
        for peer in self.peers:
            self.next_index[peer] = len(self.log)
            self.match_index[peer] = 0

    def propose(self, command, data=None):
        """Propose a new value (only if leader)."""
        if self.state != NodeState.LEADER:
            return None

        entry = LogEntry(
            term=self.current_term,
            index=len(self.log),
            command=command,
            data=data or {},
        )
        self.log.append(entry)
        return entry


class RaftCluster:
    """A cluster of Raft nodes for consensus."""

    def __init__(self, num_nodes=5):
        self.node_ids = [f"node-{i}" for i in range(num_nodes)]
        self.nodes = {}
        self.leader_id = None

        for nid in self.node_ids:
            peers = [p for p in self.node_ids if p != nid]
            self.nodes[nid] = RaftNode(nid, peers)

    def elect_leader(self, candidate_id=None):
        """Simulate a leader election."""
        if candidate_id is None:
            candidate_id = random.choice(self.node_ids)

        candidate = self.nodes[candidate_id]
        vote_request = candidate.start_election()

        votes = 1  # self-vote
        for peer_id in candidate.peers:
            response = self.nodes[peer_id].request_vote(vote_request)
            if response.vote_granted:
                votes += 1

        majority = len(self.node_ids) // 2 + 1
        if votes >= majority:
            candidate.become_leader()
            self.leader_id = candidate_id
            self._send_heartbeat()
            return True

        return False

    def _send_heartbeat(self):
        """Leader sends heartbeat to all peers."""
        if not self.leader_id:
            return

        leader = self.nodes[self.leader_id]
        for peer_id in leader.peers:
            request = AppendEntriesRequest(
                term=leader.current_term,
                leader_id=self.leader_id,
                prev_log_index=len(leader.log) - 1 if leader.log else -1,
                prev_log_term=leader.log[-1].term if leader.log else 0,
                entries=[],
                leader_commit=leader.commit_index,
            )
            self.nodes[peer_id].append_entries(request)

    def propose(self, command, data=None):
        """Propose a value through the leader."""
        if not self.leader_id:
            return None

        leader = self.nodes[self.leader_id]
        entry = leader.propose(command, data)
        if entry is None:
            return None

        # Replicate to followers
        success_count = 1
        for peer_id in leader.peers:
            request = AppendEntriesRequest(
                term=leader.current_term,
                leader_id=self.leader_id,
                prev_log_index=entry.index - 1,
                prev_log_term=leader.log[entry.index - 1].term if entry.index > 0 else 0,
                entries=[entry],
                leader_commit=leader.commit_index,
            )
            response = self.nodes[peer_id].append_entries(request)
            if response.success:
                success_count += 1
                leader.match_index[peer_id] = response.match_index

        majority = len(self.node_ids) // 2 + 1
        if success_count >= majority:
            leader.commit_index = entry.index
            return entry

        return None

    def get_cluster_state(self):
        """Get state of all nodes."""
        return {
            nid: {
                "state": node.state.value,
                "term": node.current_term,
                "log_length": len(node.log),
                "commit_index": node.commit_index,
            }
            for nid, node in self.nodes.items()
        }


if __name__ == "__main__":
    cluster = RaftCluster(num_nodes=5)

    # Elect a leader
    elected = cluster.elect_leader("node-0")
    print(f"Leader elected: {elected}, leader={cluster.leader_id}")

    # Propose values
    for i in range(5):
        entry = cluster.propose(f"set", {"key": f"k{i}", "value": f"v{i}"})
        if entry:
            print(f"Committed: term={entry.term}, index={entry.index}, cmd={entry.command}")

    print("\nCluster state:")
    for nid, state in cluster.get_cluster_state().items():
        print(f"  {nid}: {state}")
