"""This module provides the Group Bill model-controller."""
# gbill/gbill.py

from pathlib import Path
from typing import Any, Dict, List, NamedTuple
from gbill import DB_READ_ERROR, ID_ERROR
from gbill.db import DatabaseHandler


class CurrentBill(NamedTuple):
    bill: Dict[str, Any]
    error: int


class Biller:
    def __init__(self, db_path: Path) -> None:
        self._db_handler = DatabaseHandler(db_path)

    def add(self, participant: List[str], amount: float) -> CurrentBill:
        """Add a new bill to the database."""
        participant_list = []
        for _ in participant:
            _ = _.lower()
            if ',' in _:
                participant_list.extend([a.strip() for a in _.split(',') if a.strip() != ''])
            else:
                participant_list.append(_.strip())
        participant_list = [_.capitalize() for _ in participant_list]
        participant_list.sort()
        bill = {
            'Participant': participant_list,
            'Amount': amount,
        }
        read = self._db_handler.read_bills()
        if read.error == DB_READ_ERROR:
            return CurrentBill(bill, read.error)
        read.bill_list.append(bill)
        write = self._db_handler.write_bills(read.bill_list)
        return CurrentBill(bill, write.error)

    def edit_amount(self, bill_id: int, amount: float) -> CurrentBill:
        """Edit a bill's amount with the new amount"""
        read = self._db_handler.read_bills()
        if read.error:
            return CurrentBill({}, read.error)
        try:
            bill = read.bill_list[bill_id - 1]
        except IndexError:
            return CurrentBill({}, ID_ERROR)
        bill['Amount'] = amount
        write = self._db_handler.write_bills(read.bill_list)
        return CurrentBill(bill, write.error)

    def edit_participant(self, bill_id: int, participant: List[str]) -> CurrentBill:
        """Edit a bill's participant(s) with the new values"""
        participant_list = []
        for _ in participant:
            _ = _.lower()
            if ',' in _:
                participant_list.extend([a.strip() for a in _.split(',') if a.strip() != ''])
            else:
                participant_list.append(_.strip())
        participant_list = [_.capitalize() for _ in participant_list]
        participant_list.sort()
        read = self._db_handler.read_bills()
        if read.error:
            return CurrentBill({}, read.error)
        try:
            bill = read.bill_list[bill_id - 1]
        except IndexError:
            return CurrentBill({}, ID_ERROR)
        bill['Participant'] = participant_list
        write = self._db_handler.write_bills(read.bill_list)
        return CurrentBill(bill, write.error)

    def get_bill_list(self) -> List[Dict[str, Any]]:
        """Return the current bill list"""
        read = self._db_handler.read_bills()
        return read.bill_list

    def remove(self, bill_id) -> CurrentBill:
        """Remove a bill from the database using its id or index"""
        read = self._db_handler.read_bills()
        if read.error:
            return CurrentBill({}, read.error)
        try:
            bill = read.bill_list.pop(bill_id - 1)
        except IndexError:
            return CurrentBill({}, ID_ERROR)
        write = self._db_handler.write_bills(read.bill_list)
        return CurrentBill(bill, write.error)

    def remove_all(self) -> CurrentBill:
        """Remove all bills from the database."""
        write = self._db_handler.write_bills(([]))
        return CurrentBill({}, write.error)
