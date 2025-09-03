package common

import (
	"net"
	"fmt"
	"bufio"
	"strings"
	"strconv"
	"encoding/binary"
)

const BET_SPLITTER_BYTE = '\n'
const BET_SPLITTER_STR = "\n"
const BATCH_OP_CODE = 1
const WINNERS_OP_CODE = 2

type ClientSocket struct {
	conn   net.Conn
	reader *bufio.Reader
}

const BET_SPLITTER = '\n'

func NewClientSocket(address string) (*ClientSocket, error) {
	conn, err := net.Dial("tcp", address)
	if err != nil {
		return nil, err
	}
	
	return &ClientSocket{conn : conn, reader : bufio.NewReader(conn)}, nil
}

func (cs *ClientSocket) sendAll(data []byte, opCode uint8) error {
	opCodeBuf := []byte{opCode}
	packet := append(opCodeBuf, data...)
	total := 0
	size := len(packet)
    for total < size {
        n, err := cs.conn.Write(packet[total:])
        if err != nil {
            return err
        }
        total += n
    }
    return nil
}

func convertIDToUint8(id string) (uint8, error) {
	idInt, err := strconv.Atoi(id)
	if err != nil {
	    return 0, fmt.Errorf("invalid agency id: %v", err)
	}
	if idInt < 0 || idInt > 255 {
	    return 0, fmt.Errorf("agency id out of range: %d", idInt)
	}
	return uint8(idInt), nil
}

func (cs *ClientSocket) SendWinnerRequest(agencyNumber string) error {
	id, err := convertIDToUint8(agencyNumber)
	if err != nil {
		log.Errorf("action: parse_id | result: fail | error: %v", err)
		return err
	}
	log.Debugf("action: sending_winners_request | result: waiting")
	agencyBuf := []byte{id}
	err = cs.sendAll(agencyBuf, WINNERS_OP_CODE)
	if err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | error: %v", err)
		return err
	}
	log.Debugf("action: waiting_for_winners | result: success")
	return nil
}

func (cs *ClientSocket) SendBatch(bets []Bet) error {
	var sb strings.Builder
    for i, bet := range bets {
		if i > 0 {
        	sb.WriteString(BET_SPLITTER_STR)
    	}
        sb.WriteString(fmt.Sprintf("%s,%s,%s,%s,%s,%s",
            bet.AgencyID, bet.Name, bet.Surname, bet.Document, bet.Birth, bet.Number))
    }
    data := []byte(sb.String())

    if len(data) > MAX_SIZE_BATCH {
        return fmt.Errorf("batch demasiado grande: %d bytes", len(data))
    }

    size := make([]byte, 2)
    binary.BigEndian.PutUint16(size, uint16(len(data)))
	log.Debugf("action: send_batch | result: in_progress | size: %d bytes", len(data))
	err := cs.sendAll(append(size, data...), BATCH_OP_CODE)
    return err
}


func (cs *ClientSocket) ReceiveResponse() (string, error) {
	msg, err := cs.reader.ReadString(BET_SPLITTER_BYTE)
	return msg, err
}

func (cs *ClientSocket) Close() {
	cs.conn.Close()
}
