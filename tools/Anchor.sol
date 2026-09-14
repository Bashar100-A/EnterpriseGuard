// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract RingAnchor {
    event RingAnchored(
        string ringHash,
        string chainId,
        uint256 timestamp
    );

    struct Anchor {
        string ringHash;
        string chainId;
        uint256 timestamp;
    }

    mapping(uint256 => Anchor) public anchors;
    uint256 public anchorCount;

    function anchorRing(string memory ringHash, string memory chainId) public {
        anchorCount++;
        anchors[anchorCount] = Anchor(ringHash, chainId, block.timestamp);
        emit RingAnchored(ringHash, chainId, block.timestamp);
    }
}
