package common

import (
	"net"
	"fmt"
	"bufio"
	"strings"
	"encoding/binary"
)

const BET_SPLITTER_BYTE = '\n'
const BET_SPLITTER_STR = "\n"

type ClientSocket struct {
	conn   net.Conn
	reader *bufio.Reader
}

func NewClientSocket(address string) (*ClientSocket, error) {
	conn, err := net.Dial("tcp", address)
	if err != nil {
		return nil, err
	}
	
	return &ClientSocket{conn : conn, reader : bufio.NewReader(conn)}, nil
}

func (cs *ClientSocket) sendAll(data []byte) error {
	total := 0
	size := len(data)
    for total < size {
        n, err := cs.conn.Write(data[total:])
        if err != nil {
            return err
        }
        total += n
    }
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
	log.Infof("action: send_batch | result: in_progress | size: %s bytes", data)
	err := cs.sendAll(append(size, data...))
    return err
}


func (cs *ClientSocket) ReceiveResponse() (string, error) {
	msg, err := cs.reader.ReadString(BET_SPLITTER_BYTE)
	return msg, err
}

func (cs *ClientSocket) Close() {
	cs.conn.Close()
}
