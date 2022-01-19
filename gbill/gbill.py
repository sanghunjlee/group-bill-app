"""This module provides the Group Bill model-controller."""
# gbill/gbill.py

from pathlib import Path
from typing import Any, Dict, List, NamedTuple
from gbill import SUCCESS, DB_READ_ERROR, ID_ERROR
from gbill.db import DatabaseHandler


class CurrentBill(NamedTuple):
    bill: Dict[str, Any]
    error: int


class Biller:
    def __init__(self, db_path: Path) -> None:
        self._db_handler = DatabaseHandler(db_path)

    def add(self, participant: List[str], payer: str, amount: float) -> CurrentBill:
        """Add a new bill to the database."""
        participant.sort()
        bill = {
            'Participant': participant,
            'Payer': payer,
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

    def edit_payer(self, bill_id: int, payer: str) -> CurrentBill:
        """Edit a bill's payer with the new payer"""
        read = self._db_handler.read_bills()
        if read.error:
            return CurrentBill({}, read.error)
        try:
            bill = read.bill_list[bill_id - 1]
        except IndexError:
            return CurrentBill({}, ID_ERROR)
        bill['Payer'] = payer
        write = self._db_handler.write_bills(read.bill_list)
        return CurrentBill(bill, write.error)

    def edit_participant(self, bill_id: int, participant: List[str]) -> CurrentBill:
        """Edit a bill's participant(s) with the new values"""
        participant.sort()
        read = self._db_handler.read_bills()
        if read.error:
            return CurrentBill({}, read.error)
        try:
            bill = read.bill_list[bill_id - 1]
        except IndexError:
            return CurrentBill({}, ID_ERROR)
        bill['Participant'] = participant
        write = self._db_handler.write_bills(read.bill_list)
        return CurrentBill(bill, write.error)

    def get_bill_list(self) -> List[Dict[str, Any]]:
        """Return the current bill list"""
        read = self._db_handler.read_bills()
        return read.bill_list

    def get_bill(self, bill_id: int) -> CurrentBill:
        """Return a bill's value"""
        read = self._db_handler.read_bills()
        if read.error:
            return CurrentBill({}, read.error)
        try:
            bill = read.bill_list[bill_id - 1]
        except IndexError:
            return CurrentBill({}, ID_ERROR)
        return CurrentBill(bill, SUCCESS)

    def get_participant_list(self) -> List[str]:
        """Return the list of all participants"""
        ret_list = []
        read = self._db_handler.read_bills()
        for bill in read.bill_list:
            for person in bill['Participant']:
                if person not in ret_list:
                    ret_list.append(person)
        ret_list.sort()
        return ret_list

    def calculate(self) -> Dict[str, float]:
        """Return the amount each person owes"""
        calc_result = {}
        read = self._db_handler.read_bills()
        for bill in read.bill_list:
            x_amount = bill['Amount'] / (len(bill['Participant']) + 1)
            for person in bill['Participant']:
                if person in calc_result:
                    calc_result[person] += x_amount
                else:
                    calc_result[person] = x_amount
        return calc_result

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
