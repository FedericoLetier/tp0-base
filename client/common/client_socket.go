package common

import (
	"net"
	"fmt"
	"bufio"
)

type ClientSocket struct {
	conn   net.Conn
}

const BET_SPLITTER = '\n'

func NewClientSocket(address string) (*ClientSocket, error) {
	conn, err := net.Dial("tcp", address)
	if err != nil {
		return nil, err
	}
	return &ClientSocket{conn: conn}, nil
}

func (cs *ClientSocket) SendBet(bet Bet) error {
	msg := fmt.Sprintf("%s,%s,%s,%s,%s,%s\n", "1", bet.Name, bet.Surname, bet.Document, bet.Birth, bet.Number)
	data := []byte(msg)
	total := 0
	for total < len(data) {
		n, err := cs.conn.Write(data[total:])
		if err != nil {
			return err
		}
		total += n
	}
	return nil
}

func (cs *ClientSocket) ReceiveResponse() (string, error) {
	reader := bufio.NewReader(cs.conn)
	
	msg, err := reader.ReadString(BET_SPLITTER)
	if err != nil && msg != SUCCESS_RESPONSE {
		return "", err
	}

	cs.conn.Close()
	return msg, err
}

func (cs *ClientSocket) Close() {
	cs.conn.Close()
}
