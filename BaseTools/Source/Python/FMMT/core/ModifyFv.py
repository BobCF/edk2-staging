## @file
# This file is used to the implementation of Bios layout handler.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import os
from core.BiosTree import *
from core.GuidTools import GUIDTools
from core.BiosTreeNode import *
from PI.Common import *

def ModifyFvExtData(TreeNode) -> None:
    FvExtData = b''
    if TreeNode.Data.Header.ExtHeaderOffset:
        FvExtHeader = struct2stream(TreeNode.Data.ExtHeader)
        FvExtData += FvExtHeader
    if TreeNode.Data.Header.ExtHeaderOffset and TreeNode.Data.ExtEntryExist:
        FvExtEntry = struct2stream(TreeNode.Data.ExtEntry)
        FvExtData += FvExtEntry
    if FvExtData:
        InfoNode = TreeNode.Child[0]
        InfoNode.Data.Data = FvExtData + InfoNode.Data.Data[TreeNode.Data.ExtHeader.ExtHeaderSize:]
        InfoNode.Data.ModCheckSum()

class ModifyFv:
    def __init__(self, TargetFv) -> None:
        self.TargetFv = TargetFv
        self.Status = False

    ## Use for Compress the Section Data
    def ModifyFv(self) -> None:
        if self.TargetFv.Data.Free_Space:
            BlockSize = self.TargetFv.Data.Header.BlockMap[0].Length
            HaveSpace = self.TargetFv.Data.Free_Space // BlockSize
            if HaveSpace:
                NewFreeSpace = self.TargetFv.Data.Free_Space % BlockSize
                MoveOutSpace = self.TargetFv.Data.Free_Space - NewFreeSpace
                self.TargetFv.Child[-1].Data.Data = b'\xff' * NewFreeSpace
                self.TargetFv.Data.Free_Space = NewFreeSpace
                self.TargetFv.Data.Data = b''
                for item in self.TargetFv.Child:
                    if item.type == FFS_FREE_SPACE:
                        self.TargetFv.Data.Data += item.Data.Data + item.Data.PadData
                    else:
                        self.TargetFv.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                self.TargetFv.Data.Size -= MoveOutSpace
                # Modify TargetFv Data Header and ExtHeader info.
                self.TargetFv.Data.Header.FvLength = self.TargetFv.Data.Size
                self.TargetFv.Data.ModFvExt()
                self.TargetFv.Data.ModFvSize()
                self.TargetFv.Data.ModExtHeaderData()
                ModifyFvExtData(self.TargetFv)
                self.TargetFv.Data.ModCheckSum()
                self.Status = True
        else:
            print("TargetFv does not have space to move out!")
        return self.Status
